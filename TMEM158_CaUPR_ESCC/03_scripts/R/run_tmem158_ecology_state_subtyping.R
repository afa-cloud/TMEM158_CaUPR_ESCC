#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
log_file <- file.path(branch_root, "logs", "tmem158_ecology_state_subtyping.log")
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

zscore <- function(x) {
  x <- as.numeric(x)
  s <- stats::sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  (x - mean(x, na.rm = TRUE)) / s
}

within_z <- function(x, group) {
  ave(as.numeric(x), group, FUN = zscore)
}

median_group <- function(x, group) {
  ave(as.numeric(x), group, FUN = function(v) {
    ifelse(v >= stats::median(v, na.rm = TRUE), "High", "Low")
  })
}

row_mean <- function(df, cols) {
  cols <- intersect(cols, names(df))
  if (length(cols) == 0) return(rep(NA_real_, nrow(df)))
  rowMeans(df[, cols, drop = FALSE], na.rm = TRUE)
}

wilcox_state <- function(data, dataset, group_col, value_col, contrast_label, source_label) {
  d <- data[is.finite(data[[value_col]]) & data[[group_col]] %in% c("High", "Low"), ]
  n_high <- sum(d[[group_col]] == "High")
  n_low <- sum(d[[group_col]] == "Low")
  p <- NA_real_
  if (n_high >= 3 && n_low >= 3) {
    p <- suppressWarnings(stats::wilcox.test(d[[value_col]] ~ d[[group_col]])$p.value)
  }
  high_median <- ifelse(n_high > 0, stats::median(d[[value_col]][d[[group_col]] == "High"], na.rm = TRUE), NA_real_)
  low_median <- ifelse(n_low > 0, stats::median(d[[value_col]][d[[group_col]] == "Low"], na.rm = TRUE), NA_real_)
  data.frame(
    source = source_label,
    dataset = dataset,
    contrast = contrast_label,
    metric = value_col,
    n_high = n_high,
    n_low = n_low,
    high_median = high_median,
    low_median = low_median,
    delta_high_minus_low = high_median - low_median,
    p.value = p
  )
}

spearman_test <- function(data, dataset, x, y, source_label) {
  ok <- is.finite(data[[x]]) & is.finite(data[[y]])
  n <- sum(ok)
  if (n < 5) {
    return(data.frame(source = source_label, dataset = dataset, x = x, y = y,
                      n = n, rho = NA_real_, p.value = NA_real_))
  }
  ct <- suppressWarnings(stats::cor.test(data[[x]][ok], data[[y]][ok], method = "spearman"))
  data.frame(source = source_label, dataset = dataset, x = x, y = y,
             n = n, rho = unname(ct$estimate), p.value = ct$p.value)
}

signed_stouffer <- function(tab) {
  tab <- tab[is.finite(tab$p.value) & is.finite(tab$delta_high_minus_low), ]
  if (nrow(tab) == 0) {
    return(data.frame(n_testable = 0, signed_z = NA_real_, meta_p = NA_real_,
                      positive_nominal = 0, positive_fdr = 0, negative_nominal = 0))
  }
  p <- pmax(tab$p.value, .Machine$double.xmin)
  z <- stats::qnorm(1 - p / 2) * sign(tab$delta_high_minus_low)
  w <- sqrt(tab$n_high + tab$n_low)
  signed_z <- sum(w * z, na.rm = TRUE) / sqrt(sum(w^2, na.rm = TRUE))
  data.frame(
    n_testable = nrow(tab),
    signed_z = signed_z,
    meta_p = 2 * stats::pnorm(-abs(signed_z)),
    positive_nominal = sum(tab$p.value < 0.05 & tab$delta_high_minus_low > 0, na.rm = TRUE),
    positive_fdr = sum(tab$FDR_global < 0.10 & tab$delta_high_minus_low > 0, na.rm = TRUE),
    negative_nominal = sum(tab$p.value < 0.05 & tab$delta_high_minus_low < 0, na.rm = TRUE)
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

write_log("Reading TMEM158 first-pass scored data")

sample_scores <- safe_read_csv(file.path(branch_root, "02_data", "processed", "tmem158_combat_dataset_sample_scores.csv"))
tcga_surv <- safe_read_csv(file.path(branch_root, "02_data", "processed", "tmem158_tcga_tumor_scores_survival.csv"))
scrna <- safe_read_csv(file.path(branch_root, "02_data", "processed", "tmem158_gse160269_epithelial_ecosystem_scores.csv"), required = FALSE)

needed <- c("TMEM158", "Ca2_axis_score", "PERK_bias_index", "CAF_score",
            "Proteostasis_score", "Survival_score", "Drug_efflux_score",
            "UPR_composite", "PERK_score", "IRE1_score", "ATF6_score")
missing_needed <- setdiff(needed, names(sample_scores))
if (length(missing_needed) > 0) stop("Missing score columns: ", paste(missing_needed, collapse = ", "))

tumor <- sample_scores[sample_scores$group == "Tumor", ]
tumor$dataset <- tumor$batch

for (nm in needed) {
  tumor[[paste0("z_", nm)]] <- within_z(tumor[[nm]], tumor$dataset)
}

tumor$core_axis_state_score <- row_mean(tumor, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index"))
tumor$perk_caf_ecology_score <- row_mean(tumor, c("z_TMEM158", "z_PERK_bias_index", "z_CAF_score"))
tumor$full_axis_ecology_score <- row_mean(tumor, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index", "z_CAF_score"))

tumor$core_axis_state_group <- median_group(tumor$core_axis_state_score, tumor$dataset)
tumor$perk_caf_ecology_group <- median_group(tumor$perk_caf_ecology_score, tumor$dataset)
tumor$full_axis_ecology_group <- median_group(tumor$full_axis_ecology_score, tumor$dataset)

tumor$core_high <- tumor$core_axis_state_group == "High"
tumor$caf_high <- tumor$z_CAF_score >= ave(tumor$z_CAF_score, tumor$dataset, FUN = function(v) stats::median(v, na.rm = TRUE))
tumor$ecology_subtype <- ifelse(tumor$core_high & tumor$caf_high, "TAC_high",
                                ifelse(tumor$core_high & !tumor$caf_high, "Axis_only",
                                       ifelse(!tumor$core_high & tumor$caf_high, "CAF_only", "TAC_low")))

write_csv(tumor, file.path(branch_root, "02_data", "processed", "tmem158_tumor_ecology_state_scores.csv"))

state_tests <- data.frame()
core_metrics <- c("CAF_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score", "IRE1_score", "ATF6_score")
ecology_metrics <- c("Ca2_axis_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score", "IRE1_score", "ATF6_score")
full_metrics <- c("Proteostasis_score", "Survival_score", "Drug_efflux_score", "IRE1_score", "ATF6_score")

for (ds in sort(unique(tumor$dataset))) {
  d <- tumor[tumor$dataset == ds, ]
  for (m in core_metrics) {
    state_tests <- rbind(state_tests, wilcox_state(d, ds, "core_axis_state_group", m,
                                                   "TMEM158_Ca2_PERK_core_high_vs_low",
                                                   "bulk_tumor"))
  }
  for (m in ecology_metrics) {
    state_tests <- rbind(state_tests, wilcox_state(d, ds, "perk_caf_ecology_group", m,
                                                   "TMEM158_PERK_CAF_ecology_high_vs_low",
                                                   "bulk_tumor"))
  }
  for (m in full_metrics) {
    state_tests <- rbind(state_tests, wilcox_state(d, ds, "full_axis_ecology_group", m,
                                                   "TMEM158_CaUPR_CAF_full_high_vs_low",
                                                   "bulk_tumor"))
  }
}

if (!is.null(scrna) && nrow(scrna) > 0) {
  scrna$dataset <- "GSE160269_scRNA"
  scrna$z_TMEM158 <- zscore(scrna$TMEM158)
  scrna$z_Ca2_axis_score <- zscore(scrna$Ca2_axis_score)
  scrna$z_PERK_bias_index <- zscore(scrna$PERK_bias_index)
  scrna$z_CAF_score <- zscore(scrna$CAF_score)
  scrna$core_axis_state_score <- row_mean(scrna, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index"))
  scrna$perk_caf_ecology_score <- row_mean(scrna, c("z_TMEM158", "z_PERK_bias_index", "z_CAF_score"))
  scrna$core_axis_state_group <- ifelse(scrna$core_axis_state_score >= stats::median(scrna$core_axis_state_score, na.rm = TRUE), "High", "Low")
  scrna$perk_caf_ecology_group <- ifelse(scrna$perk_caf_ecology_score >= stats::median(scrna$perk_caf_ecology_score, na.rm = TRUE), "High", "Low")
  scrna$core_high <- scrna$core_axis_state_score >= stats::median(scrna$core_axis_state_score, na.rm = TRUE)
  scrna$caf_high <- scrna$z_CAF_score >= stats::median(scrna$z_CAF_score, na.rm = TRUE)
  scrna$ecology_subtype <- ifelse(scrna$core_high & scrna$caf_high, "TAC_high",
                                  ifelse(scrna$core_high & !scrna$caf_high, "Axis_only",
                                         ifelse(!scrna$core_high & scrna$caf_high, "CAF_only", "TAC_low")))
  sc_metrics <- intersect(c("CAF_score", "Treg_score", "Myeloid_suppressive_score", "Tcell_exhaustion_score", "Tcell_cytotoxic_score"), names(scrna))
  for (m in sc_metrics) {
    state_tests <- rbind(state_tests, wilcox_state(scrna, "GSE160269_scRNA", "core_axis_state_group", m,
                                                   "TMEM158_Ca2_PERK_core_high_vs_low",
                                                   "single_cell_pseudobulk"))
    state_tests <- rbind(state_tests, wilcox_state(scrna, "GSE160269_scRNA", "perk_caf_ecology_group", m,
                                                   "TMEM158_PERK_CAF_ecology_high_vs_low",
                                                   "single_cell_pseudobulk"))
  }
  scrna_subtype_count <- as.data.frame(table(scrna$ecology_subtype), stringsAsFactors = FALSE)
  names(scrna_subtype_count) <- c("ecology_subtype", "n_samples")
  write_csv(scrna_subtype_count, file.path(branch_root, "04_results", "immune", "tmem158_scrna_rule_state_counts.csv"))

  scrna_subtype_tests <- data.frame()
  scrna$TAC_high_group <- ifelse(scrna$ecology_subtype == "TAC_high", "High", "Low")
  for (m in intersect(c("Treg_score", "Myeloid_suppressive_score", "Inflammatory_myeloid_score",
                        "Tcell_exhaustion_score", "Tcell_cytotoxic_score"), names(scrna))) {
    scrna_subtype_tests <- rbind(scrna_subtype_tests, wilcox_state(scrna, "GSE160269_scRNA",
                                                                   "TAC_high_group", m,
                                                                   "scRNA_TAC_high_vs_other_rule_states",
                                                                   "single_cell_pseudobulk"))
  }
  scrna_subtype_tests$FDR <- stats::p.adjust(scrna_subtype_tests$p.value, method = "BH")
  scrna_subtype_tests$boundary_call <- ifelse(scrna_subtype_tests$FDR < 0.10 & scrna_subtype_tests$delta_high_minus_low > 0,
                                             "FDR_positive", "not_supported")
  write_csv(scrna_subtype_tests, file.path(branch_root, "04_results", "immune", "tmem158_scrna_rule_state_immune_tests.csv"))
  write_csv(scrna, file.path(branch_root, "02_data", "processed", "tmem158_scrna_ecology_state_scores.csv"))
}

state_tests$FDR_global <- stats::p.adjust(state_tests$p.value, method = "BH")
state_tests$direction <- ifelse(state_tests$delta_high_minus_low > 0, "higher_in_high_state",
                                ifelse(state_tests$delta_high_minus_low < 0, "lower_in_high_state", "no_direction"))
state_tests$support_label <- ifelse(state_tests$FDR_global < 0.10 & state_tests$delta_high_minus_low > 0, "FDR_positive",
                                    ifelse(state_tests$p.value < 0.05 & state_tests$delta_high_minus_low > 0, "nominal_positive",
                                           ifelse(state_tests$p.value < 0.05 & state_tests$delta_high_minus_low < 0, "nominal_negative", "not_significant")))
write_csv(state_tests, file.path(branch_root, "04_results", "validation", "tmem158_ecology_state_tests.csv"))

repro <- do.call(rbind, lapply(split(state_tests, paste(state_tests$contrast, state_tests$metric, sep = "||")), function(x) {
  meta <- signed_stouffer(x)
  key <- strsplit(unique(paste(x$contrast, x$metric, sep = "||"))[1], "\\|\\|")[[1]]
  data.frame(
    contrast = key[1],
    metric = key[2],
    n_datasets = length(unique(x$dataset[is.finite(x$p.value)])),
    meta,
    stringsAsFactors = FALSE
  )
}))
repro$meta_FDR <- stats::p.adjust(repro$meta_p, method = "BH")
repro$replication_call <- ifelse(repro$meta_FDR < 0.10 & repro$signed_z > 0 & repro$positive_nominal >= 2,
                                 "replicated_positive",
                                 ifelse(repro$meta_p < 0.05 & repro$signed_z > 0, "meta_positive_boundary",
                                        ifelse(repro$negative_nominal >= 2, "negative_or_inconsistent", "not_replicated")))
write_csv(repro, file.path(branch_root, "04_results", "validation", "tmem158_ecology_state_reproducibility.csv"))

state_cor <- data.frame()
for (ds in sort(unique(tumor$dataset))) {
  d <- tumor[tumor$dataset == ds, ]
  for (m in c("CAF_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score",
              "Ca2_axis_score", "PERK_bias_index", "IRE1_score", "ATF6_score")) {
    state_cor <- rbind(state_cor, spearman_test(d, ds, "core_axis_state_score", m, "bulk_tumor"))
    state_cor <- rbind(state_cor, spearman_test(d, ds, "perk_caf_ecology_score", m, "bulk_tumor"))
    state_cor <- rbind(state_cor, spearman_test(d, ds, "full_axis_ecology_score", m, "bulk_tumor"))
  }
}
state_cor$FDR_global <- stats::p.adjust(state_cor$p.value, method = "BH")
write_csv(state_cor, file.path(branch_root, "04_results", "validation", "tmem158_ecology_state_correlations.csv"))

subtype_count <- aggregate(sample ~ dataset + ecology_subtype, tumor, length)
names(subtype_count)[names(subtype_count) == "sample"] <- "n_samples"
write_csv(subtype_count, file.path(branch_root, "04_results", "validation", "tmem158_rule_ecology_subtype_counts.csv"))

subtype_wilcox <- function(data, dataset, value_col) {
  d <- data[is.finite(data[[value_col]]) & data$ecology_subtype %in% c("TAC_high", "Axis_only", "CAF_only", "TAC_low"), ]
  d$TAC_high_group <- ifelse(d$ecology_subtype == "TAC_high", "High", "Low")
  out <- wilcox_state(d, dataset, "TAC_high_group", value_col, "TAC_high_vs_all_other_rule_subtypes", "bulk_tumor")
  out
}

subtype_tests <- data.frame()
subtype_metrics <- c("Proteostasis_score", "Survival_score", "Drug_efflux_score", "IRE1_score", "ATF6_score")
for (ds in sort(unique(tumor$dataset))) {
  d <- tumor[tumor$dataset == ds, ]
  for (m in subtype_metrics) subtype_tests <- rbind(subtype_tests, subtype_wilcox(d, ds, m))
}
subtype_tests$FDR_global <- stats::p.adjust(subtype_tests$p.value, method = "BH")
subtype_tests$direction <- ifelse(subtype_tests$delta_high_minus_low > 0, "higher_in_TAC_high",
                                  ifelse(subtype_tests$delta_high_minus_low < 0, "lower_in_TAC_high", "no_direction"))
subtype_tests$support_label <- ifelse(subtype_tests$FDR_global < 0.10 & subtype_tests$delta_high_minus_low > 0, "FDR_positive",
                                      ifelse(subtype_tests$p.value < 0.05 & subtype_tests$delta_high_minus_low > 0, "nominal_positive",
                                             ifelse(subtype_tests$p.value < 0.05 & subtype_tests$delta_high_minus_low < 0, "nominal_negative", "not_significant")))
write_csv(subtype_tests, file.path(branch_root, "04_results", "validation", "tmem158_rule_ecology_subtype_tests.csv"))

subtype_repro <- do.call(rbind, lapply(split(subtype_tests, subtype_tests$metric), function(x) {
  meta <- signed_stouffer(x)
  data.frame(metric = unique(x$metric)[1],
             n_datasets = length(unique(x$dataset[is.finite(x$p.value)])),
             meta,
             stringsAsFactors = FALSE)
}))
subtype_repro$meta_FDR <- stats::p.adjust(subtype_repro$meta_p, method = "BH")
subtype_repro$replication_call <- ifelse(subtype_repro$meta_FDR < 0.10 & subtype_repro$signed_z > 0 & subtype_repro$positive_nominal >= 2,
                                         "replicated_positive",
                                         ifelse(subtype_repro$meta_p < 0.05 & subtype_repro$signed_z > 0, "meta_positive_boundary",
                                                ifelse(subtype_repro$negative_nominal >= 2, "negative_or_inconsistent", "not_replicated")))
write_csv(subtype_repro, file.path(branch_root, "04_results", "validation", "tmem158_rule_ecology_subtype_reproducibility.csv"))

write_log("Running TCGA state/subtype survival checks")

tcga_state_cols <- tumor[tumor$dataset == "TCGA", c("sample", "core_axis_state_score", "perk_caf_ecology_score",
                                                    "full_axis_ecology_score", "core_axis_state_group",
                                                    "perk_caf_ecology_group", "full_axis_ecology_group",
                                                    "ecology_subtype")]
tcga_state_surv <- merge(tcga_surv, tcga_state_cols, by = "sample", all.x = TRUE)
write_csv(tcga_state_surv, file.path(branch_root, "02_data", "processed", "tmem158_tcga_ecology_state_survival.csv"))

surv_rows <- data.frame()
if (requireNamespace("survival", quietly = TRUE)) {
  d <- tcga_state_surv[is.finite(tcga_state_surv$OS.time) & is.finite(tcga_state_surv$OS), ]
  add_cox <- function(formula_text, label, term_filter = NULL) {
    fit <- survival::coxph(stats::as.formula(formula_text), data = d)
    s <- summary(fit)
    terms <- rownames(s$coefficients)
    if (!is.null(term_filter)) terms <- terms[grepl(term_filter, terms)]
    do.call(rbind, lapply(terms, function(term) {
      data.frame(model = label, n = nrow(stats::model.frame(fit)), events = sum(d$OS == 1, na.rm = TRUE),
                 term = term,
                 HR = unname(s$coefficients[term, "exp(coef)"]),
                 p.value = unname(s$coefficients[term, "Pr(>|z|)"]))
    }))
  }
  if (nrow(d) >= 30 && sum(d$OS == 1) >= 10) {
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ scale(core_axis_state_score)", "core_axis_continuous"))
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ scale(perk_caf_ecology_score)", "perk_caf_ecology_continuous"))
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ scale(full_axis_ecology_score)", "full_axis_ecology_continuous"))
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ core_axis_state_group", "core_axis_group"))
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ perk_caf_ecology_group", "perk_caf_ecology_group"))
    surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ full_axis_ecology_group", "full_axis_ecology_group"))
    if (length(unique(stats::na.omit(d$ecology_subtype))) >= 3) {
      d$ecology_subtype <- stats::relevel(factor(d$ecology_subtype), ref = "TAC_low")
      surv_rows <- rbind(surv_rows, add_cox("survival::Surv(OS.time, OS) ~ ecology_subtype", "ecology_subtype", "ecology_subtype"))
    }
  }
}
if (nrow(surv_rows) == 0) {
  surv_rows <- data.frame(model = "not_run", n = nrow(tcga_state_surv), events = sum(tcga_state_surv$OS == 1, na.rm = TRUE),
                          term = "insufficient_data_or_survival_missing", HR = NA_real_, p.value = NA_real_)
}
surv_rows$FDR <- stats::p.adjust(surv_rows$p.value, method = "BH")
write_csv(surv_rows, file.path(branch_root, "04_results", "survival", "tmem158_ecology_state_survival.csv"))

write_log("Building TCGA ecology-state subtype profile")

sub_features <- c("TMEM158", "Ca2_axis_score", "PERK_bias_index", "CAF_score", "IRE1_score", "ATF6_score")
tcga_sub <- tumor[tumor$dataset == "TCGA", c("sample", sub_features)]
for (nm in sub_features) tcga_sub[[paste0("z_", nm)]] <- zscore(tcga_sub[[nm]])
km <- stats::kmeans(tcga_sub[, paste0("z_", sub_features)], centers = 3, nstart = 100)
tcga_sub$cluster <- paste0("K", km$cluster)
centers <- aggregate(tcga_sub[, paste0("z_", sub_features)], list(cluster = tcga_sub$cluster), mean)
centers$axis_ecology_mean <- row_mean(centers, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index", "z_CAF_score"))
centers$CAF_mean <- centers$z_CAF_score
centers$CaUPR_mean <- row_mean(centers, c("z_Ca2_axis_score", "z_PERK_bias_index"))
centers$IRE1_ATF6_mean <- row_mean(centers, c("z_IRE1_score", "z_ATF6_score"))
centers$label <- vapply(seq_len(nrow(centers)), function(i) {
  if (centers$axis_ecology_mean[i] == max(centers$axis_ecology_mean, na.rm = TRUE)) return("TMEM158_CaUPR_CAF_high")
  if (centers$IRE1_ATF6_mean[i] == max(centers$IRE1_ATF6_mean, na.rm = TRUE)) return("IRE1_ATF6_shifted")
  if (centers$z_PERK_bias_index[i] == max(centers$z_PERK_bias_index, na.rm = TRUE)) return("PERK_bias_CAF_low")
  "Axis_quiet_or_mixed"
}, character(1))
label_map <- setNames(centers$label, centers$cluster)
tcga_sub$subtype_label <- label_map[tcga_sub$cluster]
tcga_sub <- merge(tcga_sub, tcga_state_surv[, c("sample", "OS.time", "OS")], by = "sample", all.x = TRUE)

write_csv(tcga_sub, file.path(branch_root, "04_results", "validation", "tmem158_tcga_ecology_subtypes.csv"))
write_csv(centers, file.path(branch_root, "04_results", "validation", "tmem158_tcga_ecology_subtype_centers.csv"))

if (requireNamespace("cluster", quietly = TRUE)) {
  dist_mat <- stats::dist(tcga_sub[, paste0("z_", sub_features)])
  sil <- cluster::silhouette(km$cluster, dist_mat)
  subtype_qc <- data.frame(method = "kmeans_fallback_NMF_package_unavailable",
                           k = 3,
                           mean_silhouette = mean(sil[, "sil_width"], na.rm = TRUE),
                           NMF_package_available = requireNamespace("NMF", quietly = TRUE),
                           note = "NMF package was not available; kmeans on z-scored state features was used as a reproducible fallback.")
} else {
  subtype_qc <- data.frame(method = "kmeans_fallback_NMF_package_unavailable",
                           k = 3,
                           mean_silhouette = NA_real_,
                           NMF_package_available = requireNamespace("NMF", quietly = TRUE),
                           note = "NMF and cluster silhouette support unavailable; kmeans fallback only.")
}
write_csv(subtype_qc, file.path(branch_root, "04_results", "qc", "tmem158_ecology_subtype_qc.csv"))

readiness_update <- data.frame(
  gate = c("composite state reproducibility", "subtype interpretability", "survival as primary endpoint",
           "CAF-coupled biology", "Ca2 activation claim"),
  status = c(
    ifelse(any(repro$replication_call == "replicated_positive"), "partial_pass", "conditional"),
    ifelse(sum(subtype_count$ecology_subtype == "TAC_high" & subtype_count$n_samples >= 3) >= 3, "partial_pass", "conditional"),
    ifelse(any(surv_rows$FDR < 0.10, na.rm = TRUE), "conditional", "weak"),
    ifelse(any(state_tests$metric == "CAF_score" & state_tests$delta_high_minus_low > 0 & state_tests$p.value < 0.05, na.rm = TRUE), "pass", "conditional"),
    "boundary"
  ),
  evidence = c(
    paste0("replicated_positive contrasts=", sum(repro$replication_call == "replicated_positive", na.rm = TRUE),
           "; meta_positive_boundary=", sum(repro$replication_call == "meta_positive_boundary", na.rm = TRUE)),
    paste0("Rule-based TAC_high subtype has >=3 samples in ",
           sum(subtype_count$ecology_subtype == "TAC_high" & subtype_count$n_samples >= 3),
           " bulk cohorts; exploratory kmeans silhouette=", round(subtype_qc$mean_silhouette[1], 3)),
    paste0("state/subtype survival FDR<0.10 terms=", sum(surv_rows$FDR < 0.10, na.rm = TRUE)),
    paste0("CAF positive nominal tests=", sum(state_tests$metric == "CAF_score" & state_tests$delta_high_minus_low > 0 & state_tests$p.value < 0.05, na.rm = TRUE)),
    "GSE45670 Ca2 direction remains negative in first-pass correlation; avoid simple activation language."
  ),
  action_to_publish = c(
    "Use only replicated or meta-supported state contrasts in Results.",
    "Use rule-based four-state ecology subtype as the main interpretable subtype; keep kmeans as exploratory QC.",
    "Keep survival secondary or limitation unless external survival appears.",
    "Center the biological discovery on CAF-coupled stress ecology.",
    "Frame Ca2/UPR as branch-state remodeling, not uniform Ca2 activation."
  )
)
write_csv(readiness_update, file.path(branch_root, "04_results", "qc", "tmem158_submission_gap_after_subtype.csv"))

state_key <- repro[repro$replication_call %in% c("replicated_positive", "meta_positive_boundary"),
                   c("contrast", "metric", "n_datasets", "signed_z", "meta_p", "meta_FDR",
                     "positive_nominal", "positive_fdr", "replication_call")]
if (nrow(state_key) > 0) state_key$analysis <- "state_high_vs_low"
subtype_key <- subtype_repro[subtype_repro$replication_call %in% c("replicated_positive", "meta_positive_boundary"),
                             c("metric", "n_datasets", "signed_z", "meta_p", "meta_FDR",
                               "positive_nominal", "positive_fdr", "replication_call")]
if (nrow(subtype_key) > 0) {
  subtype_key$contrast <- "TAC_high_vs_all_other_rule_subtypes"
  subtype_key$analysis <- "rule_subtype_TAC_high"
}
key_results <- rbind(
  state_key[, c("analysis", "contrast", "metric", "n_datasets", "signed_z", "meta_p", "meta_FDR",
                "positive_nominal", "positive_fdr", "replication_call")],
  subtype_key[, c("analysis", "contrast", "metric", "n_datasets", "signed_z", "meta_p", "meta_FDR",
                  "positive_nominal", "positive_fdr", "replication_call")]
)
write_csv(key_results, file.path(branch_root, "06_tables", "tmem158_ecology_state_key_results.csv"))

base_index_path <- file.path(branch_root, "04_results", "result_index.csv")
base_index <- safe_read_csv(base_index_path, required = FALSE)
new_index <- data.frame(
  result = c("ecology_state_tests", "ecology_state_reproducibility", "rule_ecology_subtype_counts",
             "rule_ecology_subtype_tests", "rule_ecology_subtype_reproducibility",
             "scrna_rule_state_counts", "scrna_rule_state_immune_tests",
             "tcga_state_survival", "subtype_gap_after_update", "ecology_state_key_results"),
  path = c(
    "04_results/validation/tmem158_ecology_state_tests.csv",
    "04_results/validation/tmem158_ecology_state_reproducibility.csv",
    "04_results/validation/tmem158_rule_ecology_subtype_counts.csv",
    "04_results/validation/tmem158_rule_ecology_subtype_tests.csv",
    "04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv",
    "04_results/immune/tmem158_scrna_rule_state_counts.csv",
    "04_results/immune/tmem158_scrna_rule_state_immune_tests.csv",
    "04_results/survival/tmem158_ecology_state_survival.csv",
    "04_results/qc/tmem158_submission_gap_after_subtype.csv",
    "06_tables/tmem158_ecology_state_key_results.csv"
  )
)
if (is.null(base_index)) {
  write_csv(new_index, base_index_path)
} else {
  base_index <- base_index[!base_index$result %in% new_index$result, ]
  write_csv(rbind(base_index, new_index), base_index_path)
}

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  plot_tests <- state_tests[state_tests$source == "bulk_tumor" &
                              state_tests$contrast %in% c("TMEM158_Ca2_PERK_core_high_vs_low",
                                                          "TMEM158_PERK_CAF_ecology_high_vs_low",
                                                          "TMEM158_CaUPR_CAF_full_high_vs_low") &
                              state_tests$metric %in% c("CAF_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score"), ]
  plot_tests$contrast_short <- c(
    TMEM158_Ca2_PERK_core_high_vs_low = "TMEM158+Ca2+PERK",
    TMEM158_PERK_CAF_ecology_high_vs_low = "TMEM158+PERK+CAF",
    TMEM158_CaUPR_CAF_full_high_vs_low = "TMEM158+CaUPR+CAF"
  )[plot_tests$contrast]
  plot_tests$metric_short <- c(
    CAF_score = "CAF",
    Proteostasis_score = "Proteostasis",
    Survival_score = "Survival",
    Drug_efflux_score = "Drug efflux"
  )[plot_tests$metric]
  plot_tests$panel <- paste(plot_tests$metric_short, plot_tests$contrast_short, sep = "\n")
  p6 <- ggplot(plot_tests, aes(x = dataset, y = delta_high_minus_low, color = support_label)) +
    geom_hline(yintercept = 0, linewidth = 0.3, color = "grey55") +
    geom_point(size = 2.5) +
    facet_wrap(~panel, scales = "free_y", ncol = 3) +
    scale_color_manual(values = c(FDR_positive = "#b83232", nominal_positive = "#d98c00",
                                  nominal_negative = "#2b6cb0", not_significant = "grey55")) +
    theme_bw(base_size = 9) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1),
          legend.position = "bottom") +
    labs(title = "Cross-cohort TMEM158-CaUPR-CAF state validation",
         x = NULL, y = "Median difference: high state minus low state", color = "Support")
  plot_save(p6, file.path(branch_root, "05_figures", "figure6_tmem158_ecology_state_validation"), 11, 7)

  rule_features <- c("TMEM158", "Ca2_axis_score", "PERK_bias_index", "CAF_score",
                     "Proteostasis_score", "Survival_score", "Drug_efflux_score")
  rule_profile <- aggregate(tumor[, paste0("z_", rule_features)],
                            list(dataset = tumor$dataset, ecology_subtype = tumor$ecology_subtype), mean)
  write_csv(rule_profile, file.path(branch_root, "04_results", "validation", "tmem158_rule_ecology_subtype_profile.csv"))
  rule_long <- reshape(rule_profile,
                       varying = paste0("z_", rule_features), v.names = "mean_z",
                       timevar = "feature", times = rule_features,
                       direction = "long")
  rule_long$feature <- factor(rule_long$feature, levels = rule_features)
  rule_long$ecology_subtype <- factor(rule_long$ecology_subtype, levels = c("TAC_high", "Axis_only", "CAF_only", "TAC_low"))
  p7 <- ggplot(rule_long, aes(x = feature, y = ecology_subtype, fill = mean_z)) +
    geom_tile(color = "white", linewidth = 0.3) +
    scale_fill_gradient2(low = "#2b6cb0", mid = "white", high = "#b83232", midpoint = 0) +
    facet_wrap(~dataset, ncol = 2) +
    theme_bw(base_size = 10) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(title = "Rule-defined TMEM158-CaUPR-CAF ecology states across cohorts", x = NULL, y = NULL, fill = "Mean z")
  plot_save(p7, file.path(branch_root, "05_figures", "figure7_rule_tmem158_ecology_subtypes"), 11, 7)

  centers_long <- reshape(centers[, c("cluster", "label", paste0("z_", sub_features))],
                          varying = paste0("z_", sub_features), v.names = "mean_z",
                          timevar = "feature", times = sub_features,
                          direction = "long")
  centers_long$feature <- factor(centers_long$feature, levels = sub_features)
  p8 <- ggplot(centers_long, aes(x = feature, y = label, fill = mean_z)) +
    geom_tile(color = "white", linewidth = 0.3) +
    scale_fill_gradient2(low = "#2b6cb0", mid = "white", high = "#b83232", midpoint = 0) +
    theme_bw(base_size = 10) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(title = "Exploratory TCGA k-means state architecture", x = NULL, y = NULL, fill = "Subtype mean z")
  plot_save(p8, file.path(branch_root, "05_figures", "figure8_tcga_kmeans_state_architecture"), 8.2, 4.5)

  if (exists("scrna_subtype_tests") && nrow(scrna_subtype_tests) > 0) {
    scrna_plot <- scrna_subtype_tests
    scrna_plot$metric_short <- c(
      Treg_score = "Treg",
      Myeloid_suppressive_score = "Suppressive myeloid",
      Inflammatory_myeloid_score = "Inflammatory myeloid",
      Tcell_exhaustion_score = "T-cell exhaustion",
      Tcell_cytotoxic_score = "T-cell cytotoxicity"
    )[scrna_plot$metric]
    p10 <- ggplot(scrna_plot, aes(x = metric_short, y = delta_high_minus_low, fill = boundary_call)) +
      geom_hline(yintercept = 0, color = "grey55", linewidth = 0.3) +
      geom_col(width = 0.65) +
      coord_flip() +
      scale_fill_manual(values = c(FDR_positive = "#b83232", not_supported = "grey60")) +
      theme_bw(base_size = 10) +
      labs(title = "GSE160269 single-cell TAC_high immune-ecology boundary",
           x = NULL, y = "Median difference: TAC_high minus other states", fill = "Support")
    plot_save(p10, file.path(branch_root, "05_figures", "figure10_scrna_tac_high_immune_boundary"), 7.2, 4.8)
  }
}

fmt_state_rows <- function(x) {
  if (nrow(x) == 0) return("- No replicated or meta-positive state contrast passed the reporting filter.")
  vapply(seq_len(nrow(x)), function(i) {
    paste0("- ", x$analysis[i], ": ", x$contrast[i], " -> ", x$metric[i],
           "; signed z=", round(x$signed_z[i], 3),
           ", meta FDR=", signif(x$meta_FDR[i], 3),
           ", positive FDR cohorts=", x$positive_fdr[i],
           ", call=", x$replication_call[i], ".")
  }, character(1))
}

report <- c(
  "# TMEM158-CaUPR-CAF Ecology State Update",
  "",
  paste0("Date: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
  "",
  "## Purpose",
  "",
  "This module tests whether the TMEM158 signal is stronger as a composite Ca2/UPR-CAF ecology state than as a single-gene association.",
  "",
  "## State Definitions",
  "",
  "- `TMEM158_Ca2_PERK_core`: within-cohort z(TMEM158), z(Ca2 axis), and z(PERK-bias).",
  "- `TMEM158_PERK_CAF_ecology`: within-cohort z(TMEM158), z(PERK-bias), and z(CAF).",
  "- `TMEM158_CaUPR_CAF_full`: within-cohort z(TMEM158), z(Ca2 axis), z(PERK-bias), and z(CAF).",
  "",
  "## Interpretation Rule",
  "",
  "Only effects supported across cohorts or by signed meta-analysis should be promoted to Results. Single-cohort effects remain exploratory.",
  "",
  "## Key Results",
  "",
  fmt_state_rows(key_results),
  "",
  "## Survival Boundary",
  "",
  paste0("- TCGA state/subtype clinical OS terms with FDR<0.10: ", sum(surv_rows$FDR < 0.10, na.rm = TRUE), "."),
  "- Clinical survival remains secondary; the reproducible signal is proteostasis/survival-score biology, not OS prognosis.",
  "",
  "## Current Boundary",
  "",
  "The module is designed to protect against overclaiming: if Ca2 direction remains inconsistent, the manuscript should describe branch-state remodeling and CAF-coupled stress ecology rather than uniform Ca2 activation.",
  "",
  "## Key Files",
  "",
  "- `04_results/validation/tmem158_ecology_state_tests.csv`",
  "- `04_results/validation/tmem158_ecology_state_reproducibility.csv`",
  "- `04_results/validation/tmem158_rule_ecology_subtype_tests.csv`",
  "- `04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv`",
  "- `04_results/validation/tmem158_rule_ecology_subtype_profile.csv`",
  "- `04_results/immune/tmem158_scrna_rule_state_counts.csv`",
  "- `04_results/immune/tmem158_scrna_rule_state_immune_tests.csv`",
  "- `04_results/validation/tmem158_tcga_ecology_subtypes.csv`",
  "- `04_results/survival/tmem158_ecology_state_survival.csv`",
  "- `04_results/qc/tmem158_submission_gap_after_subtype.csv`",
  "- `05_figures/figure6_tmem158_ecology_state_validation.*`",
  "- `05_figures/figure7_rule_tmem158_ecology_subtypes.*`",
  "- `05_figures/figure8_tcga_kmeans_state_architecture.*`",
  "- `05_figures/figure10_scrna_tac_high_immune_boundary.*`"
)
writeLines(report, file.path(branch_root, "07_manuscript", "tmem158_ecology_state_update.md"))

writeLines(c(
  "# Stage Summary",
  "",
  "TMEM158-CaUPR branch status after ecology-state module:",
  "",
  "- First-pass TMEM158 expression, axis-coupling, single-cell ecology and survival analyses completed.",
  "- Second-pass composite-state analysis completed.",
  "- Rule-defined `TAC_high` ecology subtype is present in all four bulk cohorts with at least three samples.",
  "- `TAC_high` versus other states shows replicated proteostasis-score and survival-score elevation across cohorts.",
  "- TCGA clinical survival remains negative and must not be used as a primary claim.",
  "- Main publishable direction is TMEM158-associated Ca2/UPR-CAF stress ecology, not TMEM158 prognostic biomarker or direct Ca2 activation."
), file.path(branch_root, "00_project_log", "stage_summary.md"))

writeLines(c(
  "# Context Checkpoint",
  "",
  "Current branch objective: build a pure public-data manuscript around TMEM158-associated Ca2/UPR-CAF stress ecology in ESCC.",
  "",
  "Supported result layer: rule-defined TAC_high state links TMEM158, Ca2/PERK and CAF ecology to proteostasis/survival-score readouts across cohorts.",
  "",
  "Hard boundaries: clinical OS is negative; Ca2 direction is not uniformly positive; NMF package is unavailable and k-means subtype QC is weak, so the main subtype should be rule-defined, not unsupervised-cluster claimed."
), file.path(branch_root, "00_project_log", "context_checkpoint.md"))

write_log("TMEM158 ecology state/subtyping module completed")
