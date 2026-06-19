#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
raw_dir <- file.path(branch_root, "02_data", "raw", "cbioportal_tmem158")
log_file <- file.path(branch_root, "logs", "tmem158_multiomics_regulation.log")
dir.create(raw_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)

write_log <- function(msg) {
  line <- sprintf("[%s] %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), msg)
  cat(line, "\n")
  cat(line, "\n", file = log_file, append = TRUE)
}

safe_read_csv <- function(path, required = TRUE) {
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

num <- function(x) suppressWarnings(as.numeric(x))

zscore <- function(x) {
  x <- num(x)
  s <- stats::sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(NA_real_, length(x)))
  as.numeric(scale(x))
}

read_profile <- function(label) {
  path <- file.path(raw_dir, sprintf("cbioportal_esca_tcga_pan_can_atlas_2018_%s_TMEM158.csv", label))
  if (!file.exists(path) || file.info(path)$size == 0) return(data.frame(sample_short = character()))
  df <- read.csv(path, check.names = FALSE)
  df$sample_short <- df$sampleId
  out <- data.frame(sample_short = df$sample_short, value = num(df$value))
  names(out)[2] <- paste0("TMEM158_", label)
  out
}

cor_row <- function(df, x, y, label) {
  ok <- is.finite(df[[x]]) & is.finite(df[[y]])
  if (sum(ok) < 8 || length(unique(df[[x]][ok])) < 3 || length(unique(df[[y]][ok])) < 3) {
    return(data.frame(comparison = label, x = x, y = y, n = sum(ok), rho = NA_real_, p.value = NA_real_))
  }
  ct <- suppressWarnings(stats::cor.test(df[[x]][ok], df[[y]][ok], method = "spearman", exact = FALSE))
  data.frame(comparison = label, x = x, y = y, n = sum(ok), rho = unname(ct$estimate), p.value = ct$p.value)
}

wilcox_row <- function(df, value_col, group_col, positive_group, label) {
  vals <- num(df[[value_col]])
  group <- as.character(df[[group_col]])
  a <- vals[group == positive_group]
  b <- vals[group != positive_group & !is.na(group)]
  p <- if (sum(is.finite(a)) >= 3 && sum(is.finite(b)) >= 3) {
    suppressWarnings(stats::wilcox.test(a, b)$p.value)
  } else {
    NA_real_
  }
  data.frame(
    comparison = label,
    value = value_col,
    group = paste0(positive_group, "_vs_other"),
    n_positive = sum(is.finite(a)),
    n_other = sum(is.finite(b)),
    median_positive = stats::median(a, na.rm = TRUE),
    median_other = stats::median(b, na.rm = TRUE),
    delta_positive_minus_other = stats::median(a, na.rm = TRUE) - stats::median(b, na.rm = TRUE),
    p.value = p
  )
}

plot_save <- function(p, stem, width = 8, height = 5) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height)
  TRUE
}

write_log("Starting TMEM158 multi-omics regulation module")

needed <- c(
  "cbioportal_esca_tcga_pan_can_atlas_2018_gistic_TMEM158.csv",
  "cbioportal_esca_tcga_pan_can_atlas_2018_log2CNA_TMEM158.csv",
  "cbioportal_esca_tcga_pan_can_atlas_2018_rna_TMEM158.csv",
  "cbioportal_esca_tcga_pan_can_atlas_2018_mutations_TMEM158.csv",
  "cbioportal_esca_tcga_pan_can_atlas_2018_methylation_hm450_TMEM158_probe_metadata.csv",
  "cbioportal_esca_tcga_pan_can_atlas_2018_methylation_hm450_TMEM158_probes.csv"
)
missing <- needed[!file.exists(file.path(raw_dir, needed))]
if (length(missing) > 0) {
  helper <- file.path(branch_root, "03_scripts", "Python", "download_tmem158_cbioportal_inputs.py")
  py <- Sys.which("python3")
  if (nzchar(py) && file.exists(helper)) {
    write_log(paste("Downloading missing cBioPortal files:", paste(missing, collapse = ", ")))
    status <- system2(py, helper, stdout = log_file, stderr = log_file)
    write_log(paste("download_tmem158_cbioportal_inputs.py status:", status))
  } else {
    write_log("Python helper unavailable; continuing with cached files only")
  }
}

tcga_state <- safe_read_csv(file.path(branch_root, "02_data", "processed", "tmem158_tcga_ecology_state_survival.csv"))
tcga_state$sample_short <- substr(tcga_state$sample, 1, 15)

reg <- tcga_state
for (label in c("gistic", "log2CNA", "rna")) {
  prof <- read_profile(label)
  if (nrow(prof) > 0) reg <- merge(reg, prof, by = "sample_short", all.x = TRUE)
}

meth_meta_path <- file.path(raw_dir, "cbioportal_esca_tcga_pan_can_atlas_2018_methylation_hm450_TMEM158_probe_metadata.csv")
meth_path <- file.path(raw_dir, "cbioportal_esca_tcga_pan_can_atlas_2018_methylation_hm450_TMEM158_probes.csv")
meth_meta <- if (file.exists(meth_meta_path)) read.csv(meth_meta_path, check.names = FALSE) else data.frame()
meth <- if (file.exists(meth_path)) read.csv(meth_path, check.names = FALSE) else data.frame()
if (nrow(meth) > 0) {
  meth$sample_short <- meth$sampleId
  meth$methylation_beta <- num(meth$value)
  if (nrow(meth_meta) > 0) meth <- merge(meth, meth_meta, by = "stableId", all.x = TRUE)
  if (!"is_tss_probe" %in% names(meth)) meth$is_tss_probe <- FALSE
  meth$is_tss_probe <- tolower(as.character(meth$is_tss_probe)) == "true"
  all_m <- aggregate(methylation_beta ~ sample_short, meth, mean, na.rm = TRUE)
  names(all_m)[2] <- "TMEM158_methylation_mean_all_probes"
  tss <- meth[meth$is_tss_probe, , drop = FALSE]
  if (nrow(tss) == 0 && "description" %in% names(meth)) tss <- meth[grepl("TSS", meth$description, ignore.case = TRUE), , drop = FALSE]
  if (nrow(tss) > 0) {
    tss_m <- aggregate(methylation_beta ~ sample_short, tss, mean, na.rm = TRUE)
    names(tss_m)[2] <- "TMEM158_promoter_methylation"
    reg <- merge(reg, tss_m, by = "sample_short", all.x = TRUE)
  }
  reg <- merge(reg, all_m, by = "sample_short", all.x = TRUE)
}

reg$TMEM158_gistic_class <- cut(num(reg$TMEM158_gistic),
  breaks = c(-Inf, -2, -1, 0, 1, Inf),
  labels = c("Deep loss", "Loss", "Neutral", "Gain", "Amplification"),
  right = TRUE
)
reg$TMEM158_CNA_loss_score <- zscore(-num(reg$TMEM158_log2CNA))
reg$TMEM158_promoter_methylation_z <- if ("TMEM158_promoter_methylation" %in% names(reg)) zscore(reg$TMEM158_promoter_methylation) else NA_real_
reg$TMEM158_methylation_mean_z <- if ("TMEM158_methylation_mean_all_probes" %in% names(reg)) zscore(reg$TMEM158_methylation_mean_all_probes) else NA_real_
write_csv(reg, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_regulatory_matrix.csv"))

cnv_counts <- as.data.frame(table(reg$TMEM158_gistic_class, useNA = "ifany"))
names(cnv_counts) <- c("TMEM158_gistic_class", "n")
write_csv(cnv_counts, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_cnv_counts.csv"))

reg_vars <- intersect(c("TMEM158_log2CNA", "TMEM158_CNA_loss_score", "TMEM158_promoter_methylation",
                        "TMEM158_methylation_mean_all_probes"), names(reg))
outcome_vars <- intersect(c("TMEM158", "core_axis_state_score", "perk_caf_ecology_score",
                            "full_axis_ecology_score", "CAF_score", "Proteostasis_score",
                            "Survival_score", "Drug_efflux_score"), names(reg))
reg_cor <- do.call(rbind, lapply(reg_vars, function(x) {
  do.call(rbind, lapply(outcome_vars, function(y) cor_row(reg, x, y, paste0(x, " vs ", y))))
}))
if (is.null(reg_cor) || nrow(reg_cor) == 0) {
  reg_cor <- data.frame(comparison = character(), x = character(), y = character(), n = integer(), rho = numeric(), p.value = numeric())
}
reg_cor$FDR <- stats::p.adjust(reg_cor$p.value, method = "BH")
write_csv(reg_cor, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_regulatory_correlations.csv"))

cnv_group_tests <- do.call(rbind, lapply(intersect(c("TMEM158", "full_axis_ecology_score", "Proteostasis_score", "Survival_score"), names(reg)), function(v) {
  wilcox_row(reg, v, "TMEM158_gistic_class", "Gain", paste0(v, " in GISTIC gain vs other"))
}))
write_csv(cnv_group_tests, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_cnv_group_tests.csv"))

probe_cor <- data.frame()
if (nrow(meth) > 0) {
  meth_join <- merge(meth, tcga_state, by = "sample_short")
  metrics <- intersect(c("TMEM158", "core_axis_state_score", "full_axis_ecology_score", "CAF_score", "Proteostasis_score"), names(meth_join))
  probe_cor <- do.call(rbind, lapply(split(meth_join, meth_join$stableId), function(df) {
    rows <- do.call(rbind, lapply(metrics, function(metric) cor_row(df, "methylation_beta", metric, paste0(df$stableId[1], " vs ", metric))))
    meta_cols <- intersect(c("stableId", "name", "description", "transcript_id", "is_tss_probe", "alias_hit"), names(df))
    cbind(df[rep(1, nrow(rows)), meta_cols, drop = FALSE], rows)
  }))
  probe_cor$FDR_by_metric <- ave(probe_cor$p.value, probe_cor$y, FUN = function(p) stats::p.adjust(p, method = "BH"))
}
write_csv(probe_cor, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_methylation_probe_correlations.csv"))

mut_path <- file.path(raw_dir, "cbioportal_esca_tcga_pan_can_atlas_2018_mutations_TMEM158.csv")
mut <- if (file.exists(mut_path)) read.csv(mut_path, check.names = FALSE) else data.frame()
mutation_summary <- data.frame(
  item = c("mutation_records", "unique_mutated_samples"),
  value = c(nrow(mut), ifelse(nrow(mut) > 0, length(unique(mut$sampleId)), 0))
)
write_csv(mutation_summary, file.path(branch_root, "04_results", "mutation_cnv_methylation", "tmem158_cbioportal_mutation_summary.csv"))

status <- data.frame(
  item = c("module_status", "matched_tcga_samples", "cnv_values", "methylation_probes", "mutation_records",
           "cnv_expression_fdr_lt_0_10", "methylation_expression_fdr_lt_0_10"),
  value = c(
    "completed",
    nrow(reg),
    sum(is.finite(num(reg$TMEM158_log2CNA))),
    nrow(meth_meta),
    nrow(mut),
    sum(reg_cor$x == "TMEM158_log2CNA" & reg_cor$y == "TMEM158" & reg_cor$FDR < 0.10, na.rm = TRUE),
    sum(grepl("methylation", reg_cor$x) & reg_cor$y == "TMEM158" & reg_cor$FDR < 0.10, na.rm = TRUE)
  )
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_multiomics_regulation_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  plot_cor <- reg_cor[reg_cor$y %in% c("TMEM158", "full_axis_ecology_score", "Proteostasis_score") &
                        reg_cor$x %in% c("TMEM158_log2CNA", "TMEM158_CNA_loss_score", "TMEM158_methylation_mean_all_probes", "TMEM158_promoter_methylation"), ]
  if (nrow(plot_cor) > 0) {
    p9 <- ggplot(plot_cor, aes(x = x, y = y, fill = rho)) +
      geom_tile(color = "white", linewidth = 0.3) +
      scale_fill_gradient2(low = "#2b6cb0", mid = "white", high = "#b83232", midpoint = 0, na.value = "grey85") +
      theme_bw(base_size = 9) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
      labs(title = "TMEM158 regulatory context in TCGA/cBioPortal ESCA", x = NULL, y = NULL, fill = "Spearman rho")
    plot_save(p9, file.path(branch_root, "05_figures", "figure9_tmem158_multiomics_regulation"), 8, 4.8)
  }
}

report <- c(
  "# TMEM158 Multi-Omics Regulation Context",
  "",
  paste0("Date: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
  "",
  "## Purpose",
  "",
  "This public-data layer checks whether TMEM158 expression or TAC_high state can be trivially explained by TCGA/cBioPortal CNV, methylation, or mutation context.",
  "",
  "## Status",
  "",
  paste0("- Matched TCGA samples: ", nrow(reg), "."),
  paste0("- CNV values: ", sum(is.finite(num(reg$TMEM158_log2CNA))), "."),
  paste0("- Methylation probes: ", nrow(meth_meta), "."),
  paste0("- Mutation records: ", nrow(mut), "."),
  "",
  "## Boundary",
  "",
  "This layer is regulatory context only. It does not prove TMEM158 causality or protein-level mechanism.",
  "",
  "## Key Files",
  "",
  "- `04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv`",
  "- `04_results/mutation_cnv_methylation/tmem158_cbioportal_cnv_counts.csv`",
  "- `04_results/mutation_cnv_methylation/tmem158_cbioportal_methylation_probe_correlations.csv`",
  "- `04_results/qc/tmem158_multiomics_regulation_status.csv`",
  "- `05_figures/figure9_tmem158_multiomics_regulation.*`"
)
writeLines(report, file.path(branch_root, "07_manuscript", "tmem158_multiomics_regulation_update.md"))

base_index_path <- file.path(branch_root, "04_results", "result_index.csv")
base_index <- safe_read_csv(base_index_path, required = FALSE)
new_index <- data.frame(
  result = c("tmem158_multiomics_regulatory_correlations", "tmem158_multiomics_cnv_counts",
             "tmem158_multiomics_methylation_probe_correlations", "tmem158_multiomics_status"),
  path = c(
    "04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv",
    "04_results/mutation_cnv_methylation/tmem158_cbioportal_cnv_counts.csv",
    "04_results/mutation_cnv_methylation/tmem158_cbioportal_methylation_probe_correlations.csv",
    "04_results/qc/tmem158_multiomics_regulation_status.csv"
  )
)
if (is.null(base_index)) {
  write_csv(new_index, base_index_path)
} else {
  base_index <- base_index[!base_index$result %in% new_index$result, ]
  write_csv(rbind(base_index, new_index), base_index_path)
}

write_log("TMEM158 multi-omics regulation module completed")
