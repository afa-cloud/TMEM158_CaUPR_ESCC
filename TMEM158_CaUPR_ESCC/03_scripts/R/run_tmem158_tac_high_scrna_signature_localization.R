#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
project_root <- normalizePath(getwd(), mustWork = TRUE)
log_file <- file.path(branch_root, "logs", "tmem158_tac_high_scrna_signature_localization.log")
dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)

write_log <- function(msg) {
  line <- sprintf("[%s] %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), msg)
  cat(line, "\n")
  cat(line, "\n", file = log_file, append = TRUE)
}

read_csv <- function(path) {
  if (!file.exists(path)) stop("Missing required file: ", path)
  read.csv(path, check.names = FALSE)
}

write_csv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.csv(x, path, row.names = FALSE, quote = TRUE)
}

zscore <- function(x) {
  x <- as.numeric(x)
  s <- stats::sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  out <- (x - mean(x, na.rm = TRUE)) / s
  out[!is.finite(out)] <- 0
  out
}

fmt <- function(x, digits = 3) {
  x <- suppressWarnings(as.numeric(x))
  ifelse(is.finite(x), formatC(x, format = "f", digits = digits), "NA")
}

fmt_p <- function(p) {
  p <- suppressWarnings(as.numeric(p))
  ifelse(!is.finite(p), "NA", ifelse(p < 0.001, "<0.001", sprintf("%.3f", p)))
}

plot_save <- function(p, stem, width = 8, height = 5) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height)
  TRUE
}

choose_python <- function() {
  candidates <- c(
    Sys.getenv("CODEX_PYTHON", ""),
    "/Users/gdbhcx/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
    Sys.which("python3")
  )
  candidates <- candidates[nzchar(candidates)]
  candidates <- candidates[file.exists(candidates)]
  if (length(candidates) == 0) stop("No usable python3 found")
  candidates[[1]]
}

run_extractor <- function() {
  helper <- file.path(branch_root, "03_scripts", "Python", "extract_tac_high_scrna_signature_gse160269.py")
  if (!file.exists(helper)) stop("Missing helper: ", helper)
  py <- choose_python()
  write_log(sprintf("Running GSE160269 TAC_high signature extractor with %s", py))
  status <- system2(py, helper, stdout = log_file, stderr = log_file)
  if (!identical(status, 0L) && !identical(status, 0)) {
    stop("GSE160269 TAC_high signature extractor failed with status ", status)
  }
}

paired_compartment_test <- function(scores, signature, other_compartment) {
  d <- scores[scores$signature == signature & scores$compartment %in% c("Fibroblast", other_compartment), ]
  wide <- reshape(d[, c("sample", "compartment", "signature_score")],
                  idvar = "sample", timevar = "compartment", direction = "wide")
  fib_col <- "signature_score.Fibroblast"
  other_col <- paste0("signature_score.", other_compartment)
  if (!all(c(fib_col, other_col) %in% names(wide))) {
    return(data.frame(signature = signature, contrast = paste0("Fibroblast_vs_", other_compartment),
                      n_pairs = 0, median_delta = NA_real_, p.value = NA_real_))
  }
  ok <- is.finite(wide[[fib_col]]) & is.finite(wide[[other_col]])
  delta <- wide[[fib_col]][ok] - wide[[other_col]][ok]
  p <- if (sum(ok) >= 3) suppressWarnings(stats::wilcox.test(delta, mu = 0, exact = FALSE)$p.value) else NA_real_
  data.frame(signature = signature, contrast = paste0("Fibroblast_vs_", other_compartment),
             n_pairs = sum(ok), median_delta = stats::median(delta, na.rm = TRUE), p.value = p)
}

state_test <- function(scores, state, signature, compartment) {
  d <- merge(scores[scores$signature == signature & scores$compartment == compartment, ],
             state[, c("sample", "ecology_subtype", "TAC_high_group", "core_axis_state_score",
                       "perk_caf_ecology_score", "CAF_score", "TMEM158", "Ca2_axis_score",
                       "PERK_bias_index")],
             by = "sample", all.x = TRUE)
  d$group <- ifelse(d$ecology_subtype == "TAC_high", "TAC_high", "Other")
  high <- d$signature_score[d$group == "TAC_high"]
  low <- d$signature_score[d$group == "Other"]
  p <- if (sum(is.finite(high)) >= 3 && sum(is.finite(low)) >= 3) {
    suppressWarnings(stats::wilcox.test(high, low, exact = FALSE)$p.value)
  } else NA_real_
  data.frame(
    signature = signature,
    compartment = compartment,
    n_TAC_high = sum(is.finite(high)),
    n_other = sum(is.finite(low)),
    median_TAC_high = stats::median(high, na.rm = TRUE),
    median_other = stats::median(low, na.rm = TRUE),
    delta_TAC_high_minus_other = stats::median(high, na.rm = TRUE) - stats::median(low, na.rm = TRUE),
    p.value = p
  )
}

cor_row <- function(scores, state, signature, compartment, feature) {
  d <- merge(scores[scores$signature == signature & scores$compartment == compartment, ],
             state[, c("sample", feature)], by = "sample", all.x = TRUE)
  ok <- is.finite(d$signature_score) & is.finite(d[[feature]])
  if (sum(ok) >= 5) {
    ct <- suppressWarnings(stats::cor.test(d$signature_score[ok], d[[feature]][ok], method = "spearman"))
    rho <- unname(ct$estimate)
    p <- ct$p.value
  } else {
    rho <- NA_real_
    p <- NA_real_
  }
  data.frame(signature = signature, compartment = compartment, feature = feature,
             n = sum(ok), rho = rho, p.value = p)
}

write_log("Starting TAC_high single-cell signature localization module")
run_extractor()

sig_dir <- file.path(branch_root, "04_results", "scrna_signature")
gene_map <- read_csv(file.path(sig_dir, "tmem158_tac_high_scrna_signature_gene_map.csv"))
gene_means <- read_csv(file.path(sig_dir, "tmem158_tac_high_scrna_signature_gene_means.csv"))
extract_status <- read_csv(file.path(sig_dir, "tmem158_tac_high_scrna_signature_extract_status.csv"))
state <- read_csv(file.path(branch_root, "02_data", "processed", "tmem158_scrna_ecology_state_scores.csv"))

gene_map$gene <- toupper(gene_map$gene)
gene_means$gene <- toupper(gene_means$gene)
gene_means$observed <- tolower(as.character(gene_means$observed)) %in% c("true", "1", "yes")
gene_means <- gene_means[gene_means$condition == "Tumor" & gene_means$observed, ]

merged <- merge(gene_means, gene_map, by = "gene")
if (nrow(merged) == 0) stop("No matched single-cell signature genes")
merged$gene_z <- ave(merged$mean_log1p_cp10k, merged$gene, FUN = zscore)
merged$weighted_z <- merged$gene_z * merged$weight
merged$abs_weight <- abs(merged$weight)

score_sum <- aggregate(cbind(weighted_z, abs_weight) ~ signature + sample + condition + compartment + n_cells,
                       merged, sum, na.rm = TRUE)
score_sum$signature_score <- score_sum$weighted_z / score_sum$abs_weight
gene_n <- aggregate(gene ~ signature + sample + condition + compartment, merged, function(x) length(unique(x)))
names(gene_n)[names(gene_n) == "gene"] <- "n_genes_present"
scores <- merge(score_sum, gene_n, by = c("signature", "sample", "condition", "compartment"))
scores <- scores[order(scores$signature, scores$sample, scores$compartment), ]
write_csv(scores, file.path(sig_dir, "tmem158_tac_high_scrna_signature_compartment_scores.csv"))

coverage_sig_comp <- aggregate(gene ~ signature + compartment, merged, function(x) length(unique(x)))
names(coverage_sig_comp)[names(coverage_sig_comp) == "gene"] <- "n_genes_observed"
requested <- aggregate(gene ~ signature, gene_map, function(x) length(unique(x)))
names(requested)[names(requested) == "gene"] <- "n_genes_requested"
coverage_sig_comp <- merge(coverage_sig_comp, requested, by = "signature", all.x = TRUE)
coverage_sig_comp$coverage_fraction <- coverage_sig_comp$n_genes_observed / coverage_sig_comp$n_genes_requested
write_csv(coverage_sig_comp, file.path(sig_dir, "tmem158_tac_high_scrna_signature_coverage.csv"))

median_comp <- aggregate(signature_score ~ signature + compartment, scores, stats::median, na.rm = TRUE)
names(median_comp)[names(median_comp) == "signature_score"] <- "median_signature_score"
write_csv(median_comp, file.path(sig_dir, "tmem158_tac_high_scrna_signature_compartment_medians.csv"))

comp_tests <- do.call(rbind, lapply(unique(scores$signature), function(sig) {
  do.call(rbind, lapply(setdiff(sort(unique(scores$compartment)), "Fibroblast"), function(comp) {
    paired_compartment_test(scores, sig, comp)
  }))
}))
comp_tests$FDR <- stats::p.adjust(comp_tests$p.value, method = "BH")
comp_tests$call <- ifelse(comp_tests$FDR < 0.10 & comp_tests$median_delta > 0,
                          "fibroblast_higher_FDR", "not_FDR_fibroblast_higher")
write_csv(comp_tests, file.path(sig_dir, "tmem158_tac_high_scrna_signature_compartment_tests.csv"))

state_tests <- do.call(rbind, lapply(unique(scores$signature), function(sig) {
  do.call(rbind, lapply(sort(unique(scores$compartment)), function(comp) {
    state_test(scores, state, sig, comp)
  }))
}))
state_tests$FDR <- stats::p.adjust(state_tests$p.value, method = "BH")
state_tests$call <- ifelse(state_tests$FDR < 0.10 & state_tests$delta_TAC_high_minus_other > 0,
                           "TAC_high_higher_FDR", "not_FDR_TAC_high_higher")
write_csv(state_tests, file.path(sig_dir, "tmem158_tac_high_scrna_signature_state_tests.csv"))

features <- intersect(c("core_axis_state_score", "perk_caf_ecology_score", "CAF_score",
                        "TMEM158", "Ca2_axis_score", "PERK_bias_index"), names(state))
cors <- do.call(rbind, lapply(unique(scores$signature), function(sig) {
  do.call(rbind, lapply(sort(unique(scores$compartment)), function(comp) {
    do.call(rbind, lapply(features, function(feature) cor_row(scores, state, sig, comp, feature)))
  }))
}))
cors$FDR <- stats::p.adjust(cors$p.value, method = "BH")
write_csv(cors, file.path(sig_dir, "tmem158_tac_high_scrna_signature_cross_correlations.csv"))

dominant <- do.call(rbind, lapply(split(median_comp, median_comp$signature), function(d) {
  d <- d[order(-d$median_signature_score), ]
  data.frame(signature = d$signature[1], dominant_compartment = d$compartment[1],
             dominant_median_score = d$median_signature_score[1])
}))

fib_tests <- comp_tests[grep("^Fibroblast_vs_", comp_tests$contrast), ]
fib_fdr_count <- sum(fib_tests$call == "fibroblast_higher_FDR", na.rm = TRUE)
state_fib <- state_tests[state_tests$compartment == "Fibroblast", ]
top_state <- state_fib[order(state_fib$p.value), ][1, , drop = FALSE]

status <- data.frame(
  item = c(
    "module_status", "gse160269_compartments", "unique_signature_genes",
    "signature_rows", "tumor_samples_scored", "fibroblast_dominant_signatures",
    "fibroblast_higher_FDR_tests", "top_TAC_high_state_signature",
    "top_TAC_high_state_compartment", "top_TAC_high_state_FDR", "interpretation"
  ),
  value = c(
    "completed",
    paste(sort(unique(scores$compartment)), collapse = ";"),
    length(unique(gene_map$gene)),
    nrow(gene_map),
    length(unique(scores$sample)),
    sum(dominant$dominant_compartment == "Fibroblast"),
    fib_fdr_count,
    ifelse(nrow(top_state) > 0, top_state$signature[1], NA_character_),
    ifelse(nrow(top_state) > 0, top_state$compartment[1], NA_character_),
    ifelse(nrow(top_state) > 0, fmt_p(top_state$FDR[1]), NA_character_),
    "Independent GSE160269 compartment localization of TAC_high meta signatures; association only"
  )
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_tac_high_scrna_signature_localization_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  scores$compartment <- factor(scores$compartment, levels = c("Epithelial", "Fibroblast", "Myeloid", "Tcell"))
  scores$signature_label <- gsub("_", " ", scores$signature)
  p1 <- ggplot(scores, aes(x = compartment, y = signature_score, fill = compartment)) +
    geom_boxplot(width = 0.68, outlier.shape = NA, alpha = 0.82) +
    geom_jitter(width = 0.16, size = 0.9, alpha = 0.45, colour = "grey20") +
    facet_wrap(~ signature_label, scales = "free_y") +
    scale_fill_manual(values = c(Epithelial = "#4e79a7", Fibroblast = "#c44e52",
                                 Myeloid = "#59a14f", Tcell = "#8f63a9")) +
    labs(
      title = "GSE160269 compartment localization of TAC_high meta signatures",
      subtitle = "Scores use TAC_high whole-transcriptome meta genes extracted independently from single-cell matrices",
      x = NULL,
      y = "Weighted gene-z signature score"
    ) +
    theme_bw(base_size = 9) +
    theme(
      plot.title = element_text(face = "bold", size = 12),
      plot.subtitle = element_text(size = 9, colour = "grey35"),
      legend.position = "none",
      axis.text.x = element_text(angle = 25, hjust = 1),
      panel.grid.minor = element_blank(),
      strip.text = element_text(face = "bold", size = 8)
    )
  plot_save(p1, file.path(branch_root, "05_figures", "figure15_tac_high_scrna_signature_compartments"),
            width = 10, height = 5.8)

  state_plot <- merge(scores, state[, c("sample", "ecology_subtype")], by = "sample", all.x = TRUE)
  state_plot$TAC_high_status <- ifelse(state_plot$ecology_subtype == "TAC_high", "TAC_high", "Other")
  state_plot <- state_plot[state_plot$compartment %in% c("Epithelial", "Fibroblast"), ]
  state_plot$compartment <- factor(as.character(state_plot$compartment), levels = c("Epithelial", "Fibroblast"))
  state_plot$TAC_high_status <- factor(state_plot$TAC_high_status, levels = c("Other", "TAC_high"))
  state_plot$signature_label <- gsub("_", " ", state_plot$signature)
  p2 <- ggplot(state_plot, aes(x = TAC_high_status, y = signature_score, fill = TAC_high_status)) +
    geom_boxplot(width = 0.68, outlier.shape = NA, alpha = 0.85) +
    geom_jitter(width = 0.14, size = 0.9, alpha = 0.45, colour = "grey20") +
    facet_grid(signature_label ~ compartment, scales = "free_y") +
    scale_fill_manual(values = c(Other = "#9ca3af", TAC_high = "#b91c1c")) +
    labs(
      title = "Single-cell localization of TAC_high state-associated signatures",
      subtitle = "TAC_high labels are rule-defined at matched tumour-sample pseudo-bulk level",
      x = NULL,
      y = "Weighted gene-z signature score"
    ) +
    theme_bw(base_size = 9) +
    theme(
      plot.title = element_text(face = "bold", size = 12),
      plot.subtitle = element_text(size = 9, colour = "grey35"),
      legend.position = "none",
      panel.grid.minor = element_blank(),
      strip.text = element_text(face = "bold", size = 8)
    )
  plot_save(p2, file.path(branch_root, "05_figures", "figure16_tac_high_scrna_state_signature_mapping"),
            width = 8.5, height = 7.5)
}

top_comp <- dominant[order(dominant$signature), ]
top_comp_lines <- paste(sprintf("- `%s`: dominant compartment `%s` (median score %s).",
                                top_comp$signature, top_comp$dominant_compartment,
                                fmt(top_comp$dominant_median_score)), collapse = "\n")

report <- c(
  "# TAC_high Single-Cell Signature Localization",
  "",
  "This module tested whether TAC_high whole-transcriptome meta-signatures localize to epithelial tumour cells, fibroblasts/CAF, T cells or myeloid cells in independent GSE160269 single-cell matrices.",
  "",
  "## Signature Construction",
  "",
  "- `TAC_high_positive_top50`: top 50 positive genes from TAC_high-vs-other bulk meta-analysis.",
  "- `TAC_high_positive_top200`: top 200 positive genes from TAC_high-vs-other bulk meta-analysis.",
  "- `Core_CAF_interaction_positive_top200`: top 200 positive genes from the core-high by CAF-high interaction model; exploratory because interaction single-gene FDR was negative.",
  "",
  "## Key Results",
  "",
  sprintf("Unique signature genes extracted from raw GSE160269 matrices: %s.", length(unique(gene_map$gene))),
  sprintf("Tumour samples scored across compartments: %s.", length(unique(scores$sample))),
  top_comp_lines,
  sprintf("Number of paired Fibroblast-vs-other tests with Fibroblast higher at FDR<0.10: %s.", fib_fdr_count),
  ifelse(nrow(top_state) > 0,
         sprintf("Strongest TAC_high-vs-other sample-state contrast was `%s` in `%s` (FDR=%s, delta=%s).",
                 top_state$signature[1], top_state$compartment[1], fmt_p(top_state$FDR[1]),
                 fmt(top_state$delta_TAC_high_minus_other[1])),
         "No TAC_high-vs-other state contrast was available."),
  "",
  "## Interpretation Boundary",
  "",
  "This independent single-cell layer localizes TAC_high meta-signatures to compartments but does not prove cell-cell causality or TMEM158-driven transcription. If TAC_high signatures are strongest in fibroblasts, the manuscript should emphasize a CAF/ECM-dominant stress ecology rather than a tumour-cell-intrinsic programme."
)
writeLines(report, con = file.path(branch_root, "07_manuscript", "tmem158_tac_high_scrna_signature_localization_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
new_index <- data.frame(
  result = c(
    "tac_high_scrna_signature_status",
    "tac_high_scrna_signature_scores",
    "tac_high_scrna_signature_compartment_tests",
    "tac_high_scrna_signature_state_tests",
    "figure15_tac_high_scrna_signature_compartments",
    "figure16_tac_high_scrna_state_signature_mapping",
    "tac_high_scrna_signature_update"
  ),
  path = c(
    "04_results/qc/tmem158_tac_high_scrna_signature_localization_status.csv",
    "04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_scores.csv",
    "04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_tests.csv",
    "04_results/scrna_signature/tmem158_tac_high_scrna_signature_state_tests.csv",
    "05_figures/figure15_tac_high_scrna_signature_compartments.png",
    "05_figures/figure16_tac_high_scrna_state_signature_mapping.png",
    "07_manuscript/tmem158_tac_high_scrna_signature_localization_update.md"
  )
)
if (file.exists(index_path)) {
  old_index <- read.csv(index_path, check.names = FALSE)
  combined_index <- rbind(old_index, new_index)
  combined_index <- combined_index[!duplicated(combined_index$result), ]
} else {
  combined_index <- new_index
}
write_csv(combined_index, index_path)

write_log("TAC_high single-cell signature localization module completed")
