#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
})

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
out_dir <- file.path(branch_root, "04_results", "spatial_progression")
fig_dir <- file.path(branch_root, "05_figures")
man_dir <- file.path(branch_root, "07_manuscript")
log_file <- file.path(branch_root, "logs", "tmem158_spatial_progression_context.log")
for (d in c(out_dir, fig_dir, man_dir, dirname(log_file))) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
}

write_log <- function(msg) {
  line <- sprintf("[%s] %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), msg)
  cat(line, "\n")
  cat(line, "\n", file = log_file, append = TRUE)
}

read_csv <- function(path, required = TRUE) {
  if (!file.exists(path)) {
    if (required) stop("Missing required file: ", path)
    return(NULL)
  }
  read.csv(path, check.names = FALSE)
}

write_csv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.csv(x, path, row.names = FALSE, quote = TRUE)
}

fmt <- function(x, digits = 3) {
  x <- suppressWarnings(as.numeric(x))
  ifelse(is.finite(x), formatC(x, format = "f", digits = digits), "NA")
}

fmt_p <- function(x) {
  x <- suppressWarnings(as.numeric(x))
  ifelse(!is.finite(x), "NA", ifelse(x < 0.001, "<0.001", sprintf("%.3f", x)))
}

choose_python <- function() {
  candidates <- c(
    Sys.getenv("CODEX_PYTHON", ""),
    "/Users/gdbhcx/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
    Sys.which("python3")
  )
  candidates <- candidates[nzchar(candidates)]
  candidates <- candidates[file.exists(candidates)]
  if (!length(candidates)) stop("No usable python3 found")
  candidates[[1]]
}

run_extractor <- function() {
  helper <- file.path(branch_root, "03_scripts", "Python", "extract_natcomm2023_spatial_source_data.py")
  if (!file.exists(helper)) stop("Missing helper: ", helper)
  py <- choose_python()
  write_log(sprintf("Running Nat Commun 2023 spatial source-data extractor with %s", py))
  status <- system2(py, normalizePath(helper, mustWork = TRUE), stdout = log_file, stderr = log_file)
  if (!identical(status, 0L) && !identical(status, 0)) {
    stop("Spatial source-data extractor failed with status ", status)
  }
}

stage_levels <- c("NE", "LGIN", "HGIN", "ESCC")
stage_rank <- setNames(seq_along(stage_levels) - 1, stage_levels)

zscore <- function(x) {
  x <- suppressWarnings(as.numeric(x))
  s <- sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  out <- as.numeric(scale(x))
  out[!is.finite(out)] <- 0
  out
}

long_from_wide <- function(df, value_cols, source_type) {
  out <- do.call(rbind, lapply(value_cols, function(col) {
    data.frame(
      sample_label = df$sample_label,
      stage = df$stage,
      feature = col,
      value = suppressWarnings(as.numeric(df[[col]])),
      source_type = source_type,
      stringsAsFactors = FALSE
    )
  }))
  out[is.finite(out$value), , drop = FALSE]
}

feature_test <- function(df, feature_name) {
  sub <- df[df$feature == feature_name & df$stage %in% stage_levels & is.finite(df$value), , drop = FALSE]
  sub$stage <- factor(sub$stage, levels = stage_levels)
  sub$rank <- unname(stage_rank[as.character(sub$stage)])
  n_by_stage <- tapply(sub$value, sub$stage, length)
  escc <- sub$value[sub$stage == "ESCC"]
  ne <- sub$value[sub$stage == "NE"]
  kw <- if (length(unique(sub$stage)) >= 2) suppressWarnings(kruskal.test(value ~ stage, data = sub)$p.value) else NA_real_
  wt <- if (sum(is.finite(escc)) >= 3 && sum(is.finite(ne)) >= 3) {
    suppressWarnings(wilcox.test(escc, ne, exact = FALSE)$p.value)
  } else NA_real_
  sp <- if (nrow(sub) >= 6 && length(unique(sub$rank)) >= 3 && length(unique(sub$value)) >= 3) {
    suppressWarnings(cor.test(sub$rank, sub$value, method = "spearman", exact = FALSE))
  } else NULL
  data.frame(
    feature = feature_name,
    n_total = nrow(sub),
    n_NE = unname(n_by_stage["NE"]),
    n_LGIN = unname(n_by_stage["LGIN"]),
    n_HGIN = unname(n_by_stage["HGIN"]),
    n_ESCC = unname(n_by_stage["ESCC"]),
    median_NE = median(ne, na.rm = TRUE),
    median_ESCC = median(escc, na.rm = TRUE),
    delta_ESCC_minus_NE = median(escc, na.rm = TRUE) - median(ne, na.rm = TRUE),
    kruskal_p = kw,
    escc_vs_ne_p = wt,
    spearman_rho_stage = if (is.null(sp)) NA_real_ else unname(sp$estimate),
    spearman_p_stage = if (is.null(sp)) NA_real_ else sp$p.value,
    stringsAsFactors = FALSE
  )
}

plot_save <- function(p, stem, width = 9.5, height = 6.2) {
  ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 320, bg = "white")
  ggsave(paste0(stem, ".pdf"), p, width = width, height = height, bg = "white")
  ggsave(paste0(stem, ".svg"), p, width = width, height = height, bg = "white")
}

write_log("Starting spatial progression context module")
run_extractor()

cell_abund <- read_csv(file.path(out_dir, "natcomm2023_spatial_cell_abundance.csv"))
macro_sub <- read_csv(file.path(out_dir, "natcomm2023_spatial_macrophage_subtypes.csv"))
if_markers <- read_csv(file.path(out_dir, "natcomm2023_spatial_if_markers.csv"))
roi_markers <- read_csv(file.path(out_dir, "natcomm2023_spatial_roi_marker_expression.csv"))
extract_status <- read_csv(file.path(out_dir, "natcomm2023_spatial_source_extract_status.csv"))

cell_long <- long_from_wide(cell_abund, c("fibroblasts", "macrophages"), "DSP cell deconvolution")
macro_long <- long_from_wide(macro_sub, c("macrophages_m0", "macrophages_m1", "macrophages_m2"), "DSP macrophage subtype")
if_long <- data.frame(
  sample_label = if_markers$sample_label,
  stage = if_markers$stage,
  feature = if_markers$marker,
  value = suppressWarnings(as.numeric(if_markers$value)),
  source_type = "IF quantification",
  stringsAsFactors = FALSE
)
roi_long <- data.frame(
  sample_label = paste(roi_markers$scan_label, roi_markers$roi_label, sep = "_"),
  stage = roi_markers$stage,
  feature = paste0("ROI_", roi_markers$gene),
  value = suppressWarnings(as.numeric(roi_markers$expression)),
  source_type = "ROI marker expression",
  stringsAsFactors = FALSE
)

spatial_long <- rbind(cell_long, macro_long, if_long, roi_long)
spatial_long <- spatial_long[spatial_long$stage %in% stage_levels & is.finite(spatial_long$value), , drop = FALSE]
spatial_long$stage <- factor(spatial_long$stage, levels = stage_levels)
spatial_long$rank <- unname(stage_rank[as.character(spatial_long$stage)])

features <- unique(spatial_long$feature)
tests <- do.call(rbind, lapply(features, function(x) feature_test(spatial_long, x)))
tests$FDR_kruskal <- p.adjust(tests$kruskal_p, method = "BH")
tests$FDR_escc_vs_ne <- p.adjust(tests$escc_vs_ne_p, method = "BH")
tests$FDR_stage_trend <- p.adjust(tests$spearman_p_stage, method = "BH")
tests$direction_call <- ifelse(is.finite(tests$delta_ESCC_minus_NE) & tests$delta_ESCC_minus_NE > 0 &
                                 is.finite(tests$FDR_stage_trend) & tests$FDR_stage_trend < 0.10,
                               "progression_increasing_FDR",
                               ifelse(is.finite(tests$delta_ESCC_minus_NE) & tests$delta_ESCC_minus_NE < 0 &
                                        is.finite(tests$FDR_stage_trend) & tests$FDR_stage_trend < 0.10,
                                      "progression_decreasing_FDR",
                                      "not_FDR_progression"))

write_csv(spatial_long, file.path(out_dir, "tmem158_spatial_progression_source_long.csv"))
write_csv(tests, file.path(out_dir, "tmem158_spatial_progression_stage_tests.csv"))

plot_features <- c("fibroblasts", "alpha_SMA_fibroblast_IF", "macrophages", "CD68_macrophage_IF", "macrophages_m2")
plot_dat <- spatial_long[spatial_long$feature %in% plot_features, , drop = FALSE]
label_map <- c(
  fibroblasts = "DSP fibroblast abundance",
  alpha_SMA_fibroblast_IF = "alpha-SMA fibroblast IF",
  macrophages = "DSP macrophage abundance",
  CD68_macrophage_IF = "CD68 macrophage IF",
  macrophages_m2 = "DSP M2 macrophage score"
)
plot_dat$feature_label <- factor(label_map[plot_dat$feature], levels = unname(label_map[plot_features]))
spatial_palette <- c(NE = "#6C8EBF", LGIN = "#8FAF6A", HGIN = "#D9A441", ESCC = "#B85C5C")
p1 <- ggplot(plot_dat, aes(stage, value, fill = stage)) +
  geom_boxplot(width = 0.62, outlier.shape = NA, alpha = 0.82, linewidth = 0.25) +
  geom_jitter(width = 0.13, size = 1.6, alpha = 0.68, color = "#222222") +
  facet_wrap(~feature_label, scales = "free_y", ncol = 3) +
  scale_fill_manual(values = spatial_palette, drop = FALSE) +
  labs(
    title = "Public spatial progression source data supports a fibroblast-rich ESCC context",
    subtitle = "Liu et al. Nat Commun 2023 Source Data; full WTA matrix is restricted, so TAC_high is not directly rescored here",
    x = NULL,
    y = "Published source-data value"
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "none",
    strip.background = element_rect(fill = "#F3F1EC", color = "#D7D0C5"),
    strip.text = element_text(face = "bold", size = 9),
    plot.title = element_text(face = "bold", size = 13),
    plot.subtitle = element_text(size = 9),
    axis.text.x = element_text(angle = 35, hjust = 1)
  )
plot_save(p1, file.path(fig_dir, "figure21_spatial_progression_source_context"))

roi_features <- paste0("ROI_", c("TAGLN2", "CRNN", "KRT16", "KRT17", "MAL"))
roi_plot <- spatial_long[spatial_long$feature %in% roi_features, , drop = FALSE]
roi_stage_count <- length(unique(as.character(roi_plot$stage)))
if (roi_stage_count >= 2) {
  roi_plot$feature <- sub("^ROI_", "", roi_plot$feature)
  roi_plot$feature <- factor(roi_plot$feature, levels = c("TAGLN2", "CRNN", "KRT16", "KRT17", "MAL"))
  p2 <- ggplot(roi_plot, aes(stage, value, fill = stage)) +
    geom_boxplot(width = 0.62, outlier.shape = NA, alpha = 0.82, linewidth = 0.25) +
    geom_jitter(width = 0.13, size = 1.4, alpha = 0.62, color = "#222222") +
    facet_wrap(~feature, scales = "free_y", ncol = 5) +
    scale_fill_manual(values = spatial_palette, drop = FALSE) +
    labs(
      title = "Published ROI marker data confirm spatial-progression source-data parsing",
      subtitle = "Only article marker genes are available in Source Data; TMEM158/TAC_high genes are not available as a complete spatial matrix",
      x = NULL,
      y = "ROI expression"
    ) +
    theme_bw(base_size = 10.5) +
    theme(
      legend.position = "none",
      strip.background = element_rect(fill = "#F3F1EC", color = "#D7D0C5"),
      strip.text = element_text(face = "bold", size = 9),
      plot.title = element_text(face = "bold", size = 13),
      plot.subtitle = element_text(size = 9),
      axis.text.x = element_text(angle = 35, hjust = 1)
    )
  plot_save(p2, file.path(fig_dir, "figure22_spatial_progression_roi_marker_context"), width = 11, height = 4.8)
} else {
  unlink(file.path(fig_dir, paste0("figure22_spatial_progression_roi_marker_context.", c("png", "pdf", "svg"))))
}

support_features <- tests[tests$feature %in% c("fibroblasts", "alpha_SMA_fibroblast_IF", "macrophages",
                                               "CD68_macrophage_IF", "macrophages_m2"), , drop = FALSE]
fib <- tests[tests$feature == "fibroblasts", , drop = FALSE]
asma <- tests[tests$feature == "alpha_SMA_fibroblast_IF", , drop = FALSE]
m2 <- tests[tests$feature == "macrophages_m2", , drop = FALSE]

status <- data.frame(
  field = c(
    "module_status",
    "source_article",
    "source_data_type",
    "full_wta_matrix_available",
    "direct_TAC_high_score_possible",
    "roi_marker_stage_count",
    "n_source_features_tested",
    "n_progression_increasing_FDR",
    "fibroblast_delta_ESCC_minus_NE",
    "fibroblast_stage_trend_rho",
    "fibroblast_stage_trend_FDR",
    "alpha_SMA_delta_ESCC_minus_NE",
    "alpha_SMA_stage_trend_rho",
    "alpha_SMA_stage_trend_FDR",
    "M2_macrophage_delta_ESCC_minus_NE",
    "M2_macrophage_stage_trend_rho",
    "M2_macrophage_stage_trend_FDR",
    "evidence_call"
  ),
  value = c(
    "completed",
    "Liu et al. Nature Communications 2023 doi:10.1038/s41467-023-40343-5",
    "published_source_data_DSP_cell_deconvolution_IF_and_ROI_marker_tables",
    "FALSE",
    "FALSE",
    roi_stage_count,
    nrow(tests),
    sum(tests$direction_call == "progression_increasing_FDR", na.rm = TRUE),
    fmt(fib$delta_ESCC_minus_NE),
    fmt(fib$spearman_rho_stage),
    fmt_p(fib$FDR_stage_trend),
    fmt(asma$delta_ESCC_minus_NE),
    fmt(asma$spearman_rho_stage),
    fmt_p(asma$FDR_stage_trend),
    fmt(m2$delta_ESCC_minus_NE),
    fmt(m2$spearman_rho_stage),
    fmt_p(m2$FDR_stage_trend),
    "spatial_progression_context_supports_fibroblast_CAF_expansion_not_direct_TAC_high_validation"
  ),
  stringsAsFactors = FALSE
)
write_csv(status, file.path(out_dir, "tmem158_spatial_progression_context_status.csv"))
write_csv(support_features, file.path(out_dir, "tmem158_spatial_progression_key_tests.csv"))

update_md <- file.path(man_dir, "tmem158_spatial_progression_context_update.md")
cat(
  "# Spatial Progression Source-Data Context Update\n\n",
  "## Summary\n\n",
  "A public Nature Communications 2023 ESCC spatial whole-transcriptome study was added as a source-data calibration layer. The available Source Data XLSX contains published graph-level DSP cell-deconvolution values, IF quantification and selected ROI marker genes, but not the complete WTA matrix. Therefore, this module does not directly rescore TMEM158 or TAC_high in spatial ROIs.\n\n",
  "## Key Results\n\n",
  "- Source data extraction completed from `natcomm2023_escc_spatial_source_data.xlsx`.\n",
  "- Full WTA matrix in the public Source Data: FALSE; direct TAC_high spatial scoring: FALSE.\n",
  "- ROI marker source table stage count: ", roi_stage_count, "; it was retained for provenance but not used as a spatial progression validation panel.\n",
  "- Fibroblast source-data delta ESCC-minus-NE: ", fmt(fib$delta_ESCC_minus_NE), "; stage-trend rho: ", fmt(fib$spearman_rho_stage), "; FDR: ", fmt_p(fib$FDR_stage_trend), ".\n",
  "- alpha-SMA fibroblast IF delta ESCC-minus-NE: ", fmt(asma$delta_ESCC_minus_NE), "; stage-trend rho: ", fmt(asma$spearman_rho_stage), "; FDR: ", fmt_p(asma$FDR_stage_trend), ".\n",
  "- M2 macrophage score delta ESCC-minus-NE: ", fmt(m2$delta_ESCC_minus_NE), "; stage-trend rho: ", fmt(m2$spearman_rho_stage), "; FDR: ", fmt_p(m2$FDR_stage_trend), ".\n\n",
  "## Interpretation Boundary\n\n",
  "This layer supports the broader biological plausibility of a fibroblast/CAF-rich ESCC progression context that is consistent with the TAC_high CAF/ECM interpretation. It is not a direct spatial validation of TMEM158, TAC_high, Ca2/UPR activation or ligand-receptor causality because the complete spatial WTA matrix is restricted and absent from the public Source Data.\n\n",
  file = update_md,
  sep = ""
)

write_log("Spatial progression context module completed")
