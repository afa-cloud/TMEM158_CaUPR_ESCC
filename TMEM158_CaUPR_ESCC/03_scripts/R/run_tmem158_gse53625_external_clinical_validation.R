#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
  library(survival)
})

options(stringsAsFactors = FALSE)
options(timeout = max(600, getOption("timeout")))

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
project_root <- normalizePath(getwd(), mustWork = TRUE)
source_root <- file.path(project_root, "SMIM14_CaUPR_ESCC")

dirs <- list(
  source_raw = file.path(source_root, "data", "raw"),
  processed = file.path(branch_root, "02_data", "processed"),
  figures = file.path(branch_root, "05_figures"),
  qc = file.path(branch_root, "04_results", "qc"),
  validation = file.path(branch_root, "04_results", "validation"),
  survival = file.path(branch_root, "04_results", "survival"),
  manuscript = file.path(branch_root, "07_manuscript"),
  logs = file.path(branch_root, "logs"),
  scripts_py = file.path(branch_root, "03_scripts", "Python")
)
for (d in dirs) dir.create(d, recursive = TRUE, showWarnings = FALSE)

log_file <- file.path(dirs$logs, "tmem158_gse53625_external_clinical_validation.log")
if (file.exists(log_file)) invisible(file.remove(log_file))

write_log <- function(msg) {
  line <- sprintf("[%s] %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), msg)
  cat(line, "\n")
  cat(line, "\n", file = log_file, append = TRUE)
}

write_csv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.csv(x, path, row.names = FALSE, quote = TRUE, na = "")
}

safe_read_csv <- function(path, required = TRUE) {
  if (!file.exists(path)) {
    if (required) stop("Missing required file: ", path)
    return(NULL)
  }
  read.csv(path, check.names = FALSE)
}

fmt_num <- function(x, digits = 3) {
  x <- suppressWarnings(as.numeric(x))
  ifelse(is.na(x) | !is.finite(x), "NA", formatC(x, digits = digits, format = "f"))
}

fmt_p <- function(p) {
  p <- suppressWarnings(as.numeric(p))
  if (length(p) == 0 || is.na(p) || !is.finite(p)) return("NA")
  if (p < 0.001) return(formatC(p, digits = 2, format = "e"))
  formatC(p, digits = 3, format = "f")
}

status_and_exit <- function(status, detail, code = 0) {
  status_df <- data.frame(
    item = c("module_status", "detail"),
    value = c(status, detail)
  )
  write_csv(status_df, file.path(dirs$qc, "tmem158_gse53625_external_validation_status.csv"))
  writeLines(c("# GSE53625 TMEM158/TAC External Clinical Validation", "", detail),
             file.path(dirs$manuscript, "tmem158_gse53625_external_clinical_validation_update.md"))
  write_log(detail)
  quit(save = "no", status = code, runLast = FALSE)
}

zscore <- function(x) {
  x <- as.numeric(x)
  s <- stats::sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  (x - mean(x, na.rm = TRUE)) / s
}

gene_score <- function(expr, genes) {
  genes <- intersect(genes, rownames(expr))
  if (length(genes) == 0) return(rep(NA_real_, ncol(expr)))
  mat <- expr[genes, , drop = FALSE]
  if (nrow(mat) == 1) return(zscore(as.numeric(mat[1, ])))
  colMeans(t(apply(mat, 1, zscore)), na.rm = TRUE)
}

row_mean <- function(df, cols) {
  cols <- intersect(cols, names(df))
  if (length(cols) == 0) return(rep(NA_real_, nrow(df)))
  rowMeans(df[, cols, drop = FALSE], na.rm = TRUE)
}

clean_tokens <- function(line) {
  out <- scan(text = line, what = "", sep = "\t", quote = "\"", quiet = TRUE, comment.char = "")
  out[-1]
}

read_series_matrix <- function(path) {
  con <- gzfile(path, "rt")
  on.exit(close(con), add = TRUE)
  meta <- list()
  table_lines <- character()
  in_table <- FALSE
  repeat {
    line <- readLines(con, n = 1, warn = FALSE)
    if (!length(line)) break
    if (startsWith(line, "!series_matrix_table_begin")) {
      in_table <- TRUE
      next
    }
    if (startsWith(line, "!series_matrix_table_end")) break
    if (in_table) {
      table_lines <- c(table_lines, line)
      next
    }
    if (startsWith(line, "!Sample_") || startsWith(line, "!Series_platform_id")) {
      key <- sub("\t.*$", "", line)
      vals <- clean_tokens(line)
      meta[[key]] <- c(meta[[key]], list(vals))
    }
  }
  expr <- read.delim(textConnection(paste(table_lines, collapse = "\n")), check.names = FALSE)
  list(expr = expr, meta = meta)
}

clean_key <- function(x) {
  x <- tolower(trimws(x))
  x <- gsub("[^a-z0-9]+", "_", x)
  x <- gsub("^_|_$", "", x)
  sub("^tumor_loation$", "tumor_location", x)
}

parse_sample_metadata <- function(meta) {
  ids <- meta[["!Sample_geo_accession"]][[1]]
  titles <- if (!is.null(meta[["!Sample_title"]])) meta[["!Sample_title"]][[1]] else ids
  out <- data.frame(sample = ids, title = titles, stringsAsFactors = FALSE)
  chars <- meta[["!Sample_characteristics_ch1"]]
  if (length(chars)) {
    for (vals in chars) {
      for (i in seq_along(vals)) {
        token <- vals[[i]]
        if (!grepl(":", token, fixed = TRUE)) next
        key <- clean_key(sub(":.*$", "", token))
        value <- trimws(sub("^[^:]+:", "", token))
        if (!key %in% names(out)) out[[key]] <- NA_character_
        out[[key]][i] <- value
      }
    }
  }
  out$patient_id <- if ("patient_id" %in% names(out)) sub("^ec", "", out$patient_id, ignore.case = TRUE) else sub(".*patient ([0-9]+).*", "\\1", out$title)
  out$tissue_group <- ifelse(grepl("normal tissue", paste(out$title, out$tissue), ignore.case = TRUE), "Normal", "Tumor")
  out$tissue_group <- factor(out$tissue_group, levels = c("Normal", "Tumor"))
  out$age <- suppressWarnings(as.numeric(out$age))
  out$survival_months <- if ("survival_time_months" %in% names(out)) suppressWarnings(as.numeric(out$survival_time_months)) else NA_real_
  out$death_event <- if ("death_at_fu" %in% names(out)) ifelse(tolower(out$death_at_fu) == "yes", 1, ifelse(tolower(out$death_at_fu) == "no", 0, NA_real_)) else NA_real_
  out$sex <- if ("sex" %in% names(out)) tolower(out$sex) else NA_character_
  out$adjuvant_therapy <- if ("adjuvant_therapy" %in% names(out)) tolower(out$adjuvant_therapy) else NA_character_
  out$tnm_stage <- if ("tnm_stage" %in% names(out)) toupper(out$tnm_stage) else NA_character_
  out$t_stage <- if ("t_stage" %in% names(out)) toupper(out$t_stage) else NA_character_
  out$n_stage <- if ("n_stage" %in% names(out)) toupper(out$n_stage) else NA_character_
  out
}

log2_if_needed <- function(mat) {
  q99 <- suppressWarnings(stats::quantile(mat, 0.99, na.rm = TRUE))
  if (is.finite(q99) && q99 > 50) log2(mat + 1) else mat
}

aggregate_to_symbol <- function(expr_df, probe_map) {
  ids <- as.character(expr_df[[1]])
  mat <- as.matrix(expr_df[, -1, drop = FALSE])
  mode(mat) <- "numeric"
  mat <- log2_if_needed(mat)
  links <- unique(probe_map[, c("FeatureNum", "gene_symbol")])
  links$FeatureNum <- as.character(links$FeatureNum)
  idx <- match(links$FeatureNum, ids)
  keep <- !is.na(idx) & !is.na(links$gene_symbol) & nzchar(links$gene_symbol)
  if (!any(keep)) stop("No GSE53625 probes matched the TMEM158 target probe map.")
  linked <- mat[idx[keep], , drop = FALSE]
  symbols <- links$gene_symbol[keep]
  agg_sum <- rowsum(linked, group = symbols, reorder = FALSE)
  counts <- as.numeric(table(factor(symbols, levels = rownames(agg_sum))))
  sweep(agg_sum, 1, counts, "/")
}

paired_metric_summary <- function(scores, metric) {
  df <- scores[, c("patient_id", "tissue_group", metric)]
  names(df)[3] <- "value"
  tumor <- df[df$tissue_group == "Tumor", c("patient_id", "value")]
  normal <- df[df$tissue_group == "Normal", c("patient_id", "value")]
  merged <- merge(tumor, normal, by = "patient_id", suffixes = c("_tumor", "_normal"))
  merged <- merged[is.finite(merged$value_tumor) & is.finite(merged$value_normal), ]
  p <- if (nrow(merged) >= 3) {
    tryCatch(stats::wilcox.test(merged$value_tumor, merged$value_normal, paired = TRUE)$p.value, error = function(e) NA_real_)
  } else {
    NA_real_
  }
  data.frame(
    metric = metric,
    n_pairs = nrow(merged),
    tumor_median = stats::median(merged$value_tumor, na.rm = TRUE),
    normal_median = stats::median(merged$value_normal, na.rm = TRUE),
    paired_delta_median = stats::median(merged$value_tumor - merged$value_normal, na.rm = TRUE),
    paired_wilcox_p = p
  )
}

safe_cor <- function(df, x, y) {
  ok <- is.finite(df[[x]]) & is.finite(df[[y]])
  n <- sum(ok)
  if (n < 8 || stats::sd(df[[x]][ok]) == 0 || stats::sd(df[[y]][ok]) == 0) {
    return(data.frame(feature_x = x, feature_y = y, n = n, spearman_rho = NA_real_, p.value = NA_real_))
  }
  ct <- suppressWarnings(stats::cor.test(df[[x]][ok], df[[y]][ok], method = "spearman", exact = FALSE))
  data.frame(feature_x = x, feature_y = y, n = n, spearman_rho = unname(ct$estimate), p.value = ct$p.value)
}

group_contrast <- function(df, group_col, high_label, low_label, metric, contrast) {
  d <- df[is.finite(df[[metric]]) & df[[group_col]] %in% c(high_label, low_label), ]
  n_high <- sum(d[[group_col]] == high_label)
  n_low <- sum(d[[group_col]] == low_label)
  p <- if (n_high >= 3 && n_low >= 3) {
    suppressWarnings(stats::wilcox.test(d[[metric]] ~ d[[group_col]])$p.value)
  } else {
    NA_real_
  }
  high_med <- ifelse(n_high > 0, stats::median(d[[metric]][d[[group_col]] == high_label], na.rm = TRUE), NA_real_)
  low_med <- ifelse(n_low > 0, stats::median(d[[metric]][d[[group_col]] == low_label], na.rm = TRUE), NA_real_)
  data.frame(
    contrast = contrast,
    metric = metric,
    n_high = n_high,
    n_low = n_low,
    high_label = high_label,
    low_label = low_label,
    high_median = high_med,
    low_median = low_med,
    delta_high_minus_low = high_med - low_med,
    p.value = p
  )
}

cox_feature <- function(df, feature, binary = FALSE, model = "univariable") {
  d <- df[is.finite(df[[feature]]) & is.finite(df$survival_months) & is.finite(df$death_event) & df$survival_months > 0, ]
  if (nrow(d) < 30 || length(unique(d$death_event)) < 2 || stats::sd(d[[feature]], na.rm = TRUE) == 0) {
    return(data.frame(model = model, feature = feature, term = feature, n = nrow(d), events = sum(d$death_event == 1, na.rm = TRUE),
                      HR = NA_real_, conf.low = NA_real_, conf.high = NA_real_, p.value = NA_real_))
  }
  if (binary) {
    d$x <- as.numeric(d[[feature]] > 0)
    term <- "x"
  } else {
    d$x <- zscore(d[[feature]])
    term <- "x"
  }
  fit <- tryCatch(survival::coxph(survival::Surv(survival_months, death_event) ~ x, data = d), error = function(e) NULL)
  if (is.null(fit)) {
    return(data.frame(model = model, feature = feature, term = feature, n = nrow(d), events = sum(d$death_event == 1, na.rm = TRUE),
                      HR = NA_real_, conf.low = NA_real_, conf.high = NA_real_, p.value = NA_real_))
  }
  s <- summary(fit)
  data.frame(
    model = model,
    feature = feature,
    term = ifelse(binary, paste0(feature, "_positive"), paste0(feature, "_per_1sd")),
    n = nrow(stats::model.frame(fit)),
    events = sum(d$death_event == 1, na.rm = TRUE),
    HR = unname(s$conf.int[term, "exp(coef)"]),
    conf.low = unname(s$conf.int[term, "lower .95"]),
    conf.high = unname(s$conf.int[term, "upper .95"]),
    p.value = unname(s$coefficients[term, "Pr(>|z|)"])
  )
}

cox_adjusted_feature <- function(df, feature, binary = FALSE) {
  d <- df[is.finite(df[[feature]]) & is.finite(df$survival_months) & is.finite(df$death_event) & df$survival_months > 0, ]
  d <- d[is.finite(d$age) & !is.na(d$sex) & !is.na(d$tnm_stage) & !is.na(d$adjuvant_therapy), ]
  if (nrow(d) < 60 || length(unique(d$death_event)) < 2) return(NULL)
  d$x <- if (binary) as.numeric(d[[feature]] > 0) else zscore(d[[feature]])
  d$sex <- factor(d$sex)
  d$tnm_stage <- factor(d$tnm_stage, levels = c("I", "II", "III", "IV"))
  d$adjuvant_therapy <- factor(d$adjuvant_therapy)
  fit <- tryCatch(survival::coxph(survival::Surv(survival_months, death_event) ~ x + age + sex + tnm_stage + adjuvant_therapy, data = d), error = function(e) NULL)
  if (is.null(fit)) return(NULL)
  s <- summary(fit)
  term <- "x"
  data.frame(
    model = "age_sex_TNM_adjuvant_adjusted",
    feature = feature,
    term = ifelse(binary, paste0(feature, "_positive"), paste0(feature, "_per_1sd")),
    n = nrow(stats::model.frame(fit)),
    events = sum(d$death_event == 1, na.rm = TRUE),
    HR = unname(s$conf.int[term, "exp(coef)"]),
    conf.low = unname(s$conf.int[term, "lower .95"]),
    conf.high = unname(s$conf.int[term, "upper .95"]),
    p.value = unname(s$coefficients[term, "Pr(>|z|)"])
  )
}

plot_save_multi <- function(p, stem, width = 11, height = 7) {
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 320, bg = "white")
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height, bg = "white")
  if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite(paste0(stem, ".svg"), width = width, height = height, bg = "white")
    print(p)
    grDevices::dev.off()
  } else {
    grDevices::svg(paste0(stem, ".svg"), width = width, height = height, bg = "white")
    print(p)
    grDevices::dev.off()
  }
}

write_log("Building or refreshing TMEM158 GSE53625 probe map")
map_script <- file.path(dirs$scripts_py, "build_tmem158_gse53625_probe_map.py")
if (!file.exists(map_script)) status_and_exit("skipped", "TMEM158 GSE53625 probe-map builder is missing.")
map_status <- system2("python3", map_script)
probe_map_path <- file.path(dirs$processed, "gse53625_tmem158_probe_gene_map.csv")
if (!identical(map_status, 0L) || !file.exists(probe_map_path)) {
  status_and_exit("skipped", "TMEM158 GSE53625 probe sequence reannotation failed; module skipped without interrupting workflow.")
}

series_path <- file.path(dirs$source_raw, "GSE53625_series_matrix.txt.gz")
if (!file.exists(series_path)) status_and_exit("skipped", "GSE53625 series matrix not found in SMIM14 source branch.")

gene_sets <- list(
  Ca2_axis_score = c("STIM1", "ORAI1", "ATP2A2", "ITPR1", "ITPR2", "ITPR3"),
  PERK_score = c("EIF2AK3", "ATF4", "DDIT3"),
  IRE1_score = c("ERN1", "XBP1"),
  ATF6_score = c("ATF6"),
  CAF_score = c("ACTA2", "FAP", "COL1A1", "COL1A2", "CXCL12", "TAGLN", "PDPN", "DCN"),
  Proteostasis_score = c("HSPA5", "HSP90B1", "PDIA4", "DNAJB9", "HERPUD1"),
  Survival_score = c("BIRC5", "BCL2", "BCL2L1", "MCL1"),
  Drug_efflux_score = c("ABCC1", "ABCB1", "ABCG2"),
  ECM_integrin_bridge_score = c("POSTN", "COL1A1", "COL1A2", "COL3A1", "COL6A2", "COL6A3", "FN1", "ITGA5", "ITGB1", "ITGAV", "ITGB3", "MIF", "CXCR4", "INHBA", "ACVR2A"),
  Residual_stress_score = c("CHST7", "PTDSS1", "MAFG", "NFE2L2", "OSGIN1", "TOMM22", "BDNF", "HK1", "SPRYD7", "WNT5A", "TUFT1", "DUSP14", "SCAMP1", "ADM", "ABCB6", "GSTO1", "SLC3A2")
)

probe_map <- safe_read_csv(probe_map_path)
probe_status <- safe_read_csv(file.path(dirs$qc, "tmem158_gse53625_probe_mapping_status.csv"), required = FALSE)
if (!is.null(probe_status) && nrow(probe_status) > 0) {
  requested_probe_targets_n <- nrow(probe_status)
  mapped_probe_targets_n <- sum(probe_status$matched == "yes", na.rm = TRUE)
  missing_probe_targets <- probe_status$gene_symbol[probe_status$matched != "yes"]
} else {
  requested_probe_targets_n <- length(unique(probe_map$gene_symbol))
  mapped_probe_targets_n <- length(unique(probe_map$gene_symbol))
  missing_probe_targets <- character()
}
obj <- read_series_matrix(series_path)
sample_meta <- parse_sample_metadata(obj$meta)
expr <- aggregate_to_symbol(obj$expr, probe_map)
common_samples <- intersect(colnames(expr), sample_meta$sample)
expr <- expr[, common_samples, drop = FALSE]
sample_meta <- sample_meta[match(common_samples, sample_meta$sample), ]

coverage <- data.frame(
  signature = names(gene_sets),
  requested_genes = vapply(gene_sets, paste, collapse = ";", FUN.VALUE = character(1)),
  detected_genes = vapply(gene_sets, function(g) paste(intersect(g, rownames(expr)), collapse = ";"), character(1)),
  missing_genes = vapply(gene_sets, function(g) paste(setdiff(g, rownames(expr)), collapse = ";"), character(1)),
  n_requested = vapply(gene_sets, length, integer(1)),
  n_detected = vapply(gene_sets, function(g) length(intersect(g, rownames(expr))), integer(1))
)
write_csv(coverage, file.path(dirs$validation, "tmem158_gse53625_signature_coverage.csv"))

scores <- data.frame(
  sample = colnames(expr),
  patient_id = sample_meta$patient_id,
  tissue_group = sample_meta$tissue_group,
  age = sample_meta$age,
  sex = sample_meta$sex,
  tobacco_use = if ("tobacco_use" %in% names(sample_meta)) sample_meta$tobacco_use else NA_character_,
  alcohol_use = if ("alcohol_use" %in% names(sample_meta)) sample_meta$alcohol_use else NA_character_,
  tumor_location = if ("tumor_location" %in% names(sample_meta)) sample_meta$tumor_location else NA_character_,
  tumor_grade = if ("tumor_grade" %in% names(sample_meta)) sample_meta$tumor_grade else NA_character_,
  t_stage = sample_meta$t_stage,
  n_stage = sample_meta$n_stage,
  tnm_stage = sample_meta$tnm_stage,
  adjuvant_therapy = sample_meta$adjuvant_therapy,
  survival_months = sample_meta$survival_months,
  death_event = sample_meta$death_event,
  TMEM158 = if ("TMEM158" %in% rownames(expr)) as.numeric(expr["TMEM158", ]) else NA_real_
)

for (nm in names(gene_sets)) scores[[nm]] <- gene_score(expr, gene_sets[[nm]])
scores$UPR_composite <- rowMeans(scores[, c("PERK_score", "IRE1_score", "ATF6_score")], na.rm = TRUE)
scores$PERK_bias_index <- scores$PERK_score - rowMeans(scores[, c("IRE1_score", "ATF6_score")], na.rm = TRUE)
write_csv(scores, file.path(dirs$processed, "tmem158_gse53625_clinical_sample_scores.csv"))

tumor_scores <- scores[scores$tissue_group == "Tumor", ]
for (nm in c("TMEM158", "Ca2_axis_score", "PERK_bias_index", "CAF_score")) {
  tumor_scores[[paste0("z_", nm)]] <- zscore(tumor_scores[[nm]])
}
tumor_scores$core_axis_state_score <- row_mean(tumor_scores, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index"))
tumor_scores$full_axis_ecology_score <- row_mean(tumor_scores, c("z_TMEM158", "z_Ca2_axis_score", "z_PERK_bias_index", "z_CAF_score"))
tumor_scores$core_high <- tumor_scores$core_axis_state_score >= stats::median(tumor_scores$core_axis_state_score, na.rm = TRUE)
tumor_scores$caf_high <- tumor_scores$z_CAF_score >= stats::median(tumor_scores$z_CAF_score, na.rm = TRUE)
tumor_scores$ecology_subtype <- ifelse(tumor_scores$core_high & tumor_scores$caf_high, "TAC_high",
                                       ifelse(tumor_scores$core_high & !tumor_scores$caf_high, "Axis_only",
                                              ifelse(!tumor_scores$core_high & tumor_scores$caf_high, "CAF_only", "TAC_low")))
tumor_scores$TAC_high_indicator <- as.integer(tumor_scores$ecology_subtype == "TAC_high")
write_csv(tumor_scores, file.path(dirs$processed, "tmem158_gse53625_tumor_tac_scores_survival.csv"))

metrics <- c("TMEM158", "Ca2_axis_score", "PERK_score", "IRE1_score", "ATF6_score", "UPR_composite",
             "PERK_bias_index", "CAF_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score",
             "ECM_integrin_bridge_score", "Residual_stress_score")
paired_summary <- do.call(rbind, lapply(metrics, function(m) paired_metric_summary(scores, m)))
paired_summary$FDR <- stats::p.adjust(paired_summary$paired_wilcox_p, method = "BH")
write_csv(paired_summary, file.path(dirs$validation, "tmem158_gse53625_paired_tumor_normal_tests.csv"))

cor_metrics <- setdiff(metrics, "TMEM158")
cor_rows <- do.call(rbind, lapply(cor_metrics, function(m) safe_cor(tumor_scores, "TMEM158", m)))
cor_rows$FDR <- stats::p.adjust(cor_rows$p.value, method = "BH")
write_csv(cor_rows, file.path(dirs$validation, "tmem158_gse53625_tumor_correlations.csv"))

contrast_metrics <- c("CAF_score", "Proteostasis_score", "Survival_score", "Drug_efflux_score",
                      "ECM_integrin_bridge_score", "Residual_stress_score", "UPR_composite", "PERK_bias_index")
tumor_scores$TAC_vs_other <- ifelse(tumor_scores$ecology_subtype == "TAC_high", "TAC_high", "Other")
contrast_rows <- data.frame()
for (metric in contrast_metrics) {
  contrast_rows <- rbind(contrast_rows, group_contrast(tumor_scores, "TAC_vs_other", "TAC_high", "Other", metric, "TAC_high_vs_other"))
  contrast_rows <- rbind(contrast_rows, group_contrast(tumor_scores, "ecology_subtype", "TAC_high", "CAF_only", metric, "TAC_high_vs_CAF_only"))
  contrast_rows <- rbind(contrast_rows, group_contrast(tumor_scores, "ecology_subtype", "TAC_high", "Axis_only", metric, "TAC_high_vs_Axis_only"))
}
contrast_rows$FDR <- stats::p.adjust(contrast_rows$p.value, method = "BH")
contrast_rows$support_label <- ifelse(contrast_rows$FDR < 0.10 & contrast_rows$delta_high_minus_low > 0, "FDR_positive",
                                      ifelse(contrast_rows$p.value < 0.05 & contrast_rows$delta_high_minus_low > 0, "nominal_positive",
                                             ifelse(contrast_rows$p.value < 0.05 & contrast_rows$delta_high_minus_low < 0, "nominal_negative", "not_significant")))
write_csv(contrast_rows, file.path(dirs$validation, "tmem158_gse53625_tac_state_contrasts.csv"))

subtype_counts <- as.data.frame(table(tumor_scores$ecology_subtype), stringsAsFactors = FALSE)
names(subtype_counts) <- c("ecology_subtype", "n_tumor_samples")
write_csv(subtype_counts, file.path(dirs$validation, "tmem158_gse53625_tac_state_counts.csv"))

cox_features <- c("TMEM158", "core_axis_state_score", "full_axis_ecology_score", "CAF_score",
                  "Proteostasis_score", "Drug_efflux_score", "ECM_integrin_bridge_score",
                  "Residual_stress_score", "TAC_high_indicator")
cox_rows <- do.call(rbind, lapply(cox_features, function(f) cox_feature(tumor_scores, f, binary = f == "TAC_high_indicator")))
adj_rows <- do.call(rbind, lapply(c("TMEM158", "full_axis_ecology_score", "TAC_high_indicator"), function(f) {
  cox_adjusted_feature(tumor_scores, f, binary = f == "TAC_high_indicator")
}))
if (!is.null(adj_rows) && nrow(adj_rows) > 0) cox_rows <- rbind(cox_rows, adj_rows)
cox_rows$FDR_univariable <- NA_real_
u <- cox_rows$model == "univariable"
cox_rows$FDR_univariable[u] <- stats::p.adjust(cox_rows$p.value[u], method = "BH")
write_csv(cox_rows, file.path(dirs$survival, "tmem158_gse53625_survival_cox.csv"))

metric_labels <- c(
  TMEM158 = "TMEM158",
  Ca2_axis_score = "Ca2 axis",
  PERK_score = "PERK",
  IRE1_score = "IRE1",
  ATF6_score = "ATF6",
  UPR_composite = "UPR composite",
  PERK_bias_index = "PERK bias",
  CAF_score = "CAF",
  Proteostasis_score = "Proteostasis",
  Survival_score = "Survival",
  Drug_efflux_score = "Drug efflux",
  ECM_integrin_bridge_score = "ECM-integrin bridge",
  Residual_stress_score = "Residual stress",
  core_axis_state_score = "Core axis",
  full_axis_ecology_score = "Full TAC score",
  TAC_high_indicator = "TAC high"
)

p1 <- ggplot(scores[is.finite(scores$TMEM158), ], aes(x = tissue_group, y = TMEM158, group = patient_id)) +
  geom_line(alpha = 0.12, color = "grey55", linewidth = 0.25) +
  geom_boxplot(aes(group = tissue_group), width = 0.48, outlier.shape = NA, fill = "white", color = "grey25") +
  geom_jitter(aes(color = tissue_group), width = 0.12, alpha = 0.55, size = 0.8, show.legend = FALSE) +
  scale_color_manual(values = c(Normal = "#3F7D7D", Tumor = "#B04A3D")) +
  labs(title = "A  TMEM158 paired expression", x = NULL, y = "log2 expression") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold"))

paired_plot <- paired_summary[paired_summary$metric %in% c("TMEM158", "Ca2_axis_score", "CAF_score", "ECM_integrin_bridge_score", "Residual_stress_score", "Drug_efflux_score"), ]
paired_plot$metric_label <- factor(metric_labels[paired_plot$metric], levels = rev(metric_labels[paired_plot$metric]))
paired_plot$fdr_label <- ifelse(paired_plot$FDR < 0.10, "FDR < 0.10", "FDR >= 0.10")
p2 <- ggplot(paired_plot, aes(x = metric_label, y = paired_delta_median, fill = fdr_label)) +
  geom_col(width = 0.65, color = "grey25") +
  geom_hline(yintercept = 0, linewidth = 0.3, color = "grey45") +
  coord_flip() +
  scale_fill_manual(values = c("FDR < 0.10" = "#B04A3D", "FDR >= 0.10" = "#AEB7C2")) +
  labs(title = "B  Paired tumour-normal shifts", x = NULL, y = "median paired delta") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold"), legend.position = "bottom", legend.title = element_blank())

state_plot <- contrast_rows[contrast_rows$contrast == "TAC_high_vs_other" &
                              contrast_rows$metric %in% c("CAF_score", "Proteostasis_score", "Drug_efflux_score", "ECM_integrin_bridge_score", "Residual_stress_score"), ]
state_plot$metric_label <- factor(metric_labels[state_plot$metric], levels = rev(metric_labels[state_plot$metric]))
state_plot$fdr_label <- ifelse(state_plot$FDR < 0.10, "FDR < 0.10", ifelse(state_plot$p.value < 0.05, "P < 0.05", "not sig."))
p3 <- ggplot(state_plot, aes(x = metric_label, y = delta_high_minus_low, fill = fdr_label)) +
  geom_col(width = 0.65, color = "grey25") +
  geom_hline(yintercept = 0, linewidth = 0.3, color = "grey45") +
  coord_flip() +
  scale_fill_manual(values = c("FDR < 0.10" = "#B04A3D", "P < 0.05" = "#D98C00", "not sig." = "#AEB7C2")) +
  labs(title = "C  TAC_high external state contrast", x = NULL, y = "median delta vs other tumours") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold"), legend.position = "bottom", legend.title = element_blank())

forest_df <- cox_rows[cox_rows$model == "univariable" & cox_rows$feature %in% c("TMEM158", "full_axis_ecology_score", "CAF_score", "Residual_stress_score", "ECM_integrin_bridge_score", "TAC_high_indicator"), ]
forest_df <- forest_df[is.finite(forest_df$HR) & is.finite(forest_df$conf.low) & is.finite(forest_df$conf.high), ]
forest_df$feature_label <- factor(metric_labels[forest_df$feature], levels = rev(metric_labels[forest_df$feature]))
p4 <- ggplot(forest_df, aes(x = HR, y = feature_label)) +
  geom_vline(xintercept = 1, color = "grey55", linewidth = 0.35) +
  geom_errorbar(aes(xmin = conf.low, xmax = conf.high), width = 0.16, color = "grey30", orientation = "y") +
  geom_point(size = 2.2, color = "#1B365D") +
  scale_x_log10() +
  labs(title = "D  Tumour-only overall survival Cox", x = "HR per 1 s.d. or TAC_high", y = NULL) +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold"))

if (requireNamespace("patchwork", quietly = TRUE)) {
  combined <- (p1 + p2) / (p3 + p4) + patchwork::plot_annotation(
    title = "GSE53625 external clinical calibration of TMEM158-associated TAC_high",
    subtitle = "Sequence-reannotated 179-pair ESCC cohort; association analysis only"
  )
} else {
  combined <- p1
  write_log("patchwork unavailable; saved panel A only")
}
plot_save_multi(combined, file.path(dirs$figures, "figure24_gse53625_tmem158_tac_external_validation"), width = 11.5, height = 7.6)

get_row <- function(tab, col, value) {
  out <- tab[tab[[col]] == value, , drop = FALSE]
  if (nrow(out) == 0) return(NULL)
  out[1, , drop = FALSE]
}
value_or_na <- function(x) if (is.null(x) || length(x) == 0) NA else x

smim_pair <- get_row(paired_summary, "metric", "TMEM158")
residual_pair <- get_row(paired_summary, "metric", "Residual_stress_score")
ecm_pair <- get_row(paired_summary, "metric", "ECM_integrin_bridge_score")
tac_res <- contrast_rows[contrast_rows$contrast == "TAC_high_vs_other" & contrast_rows$metric == "Residual_stress_score", , drop = FALSE]
tac_ecm <- contrast_rows[contrast_rows$contrast == "TAC_high_vs_other" & contrast_rows$metric == "ECM_integrin_bridge_score", , drop = FALSE]
tmem_cox <- cox_rows[cox_rows$model == "univariable" & cox_rows$feature == "TMEM158", , drop = FALSE]
tac_cox <- cox_rows[cox_rows$model == "univariable" & cox_rows$feature == "TAC_high_indicator", , drop = FALSE]
full_cox <- cox_rows[cox_rows$model == "univariable" & cox_rows$feature == "full_axis_ecology_score", , drop = FALSE]

status_df <- data.frame(
  item = c(
    "module_status", "dataset", "platform", "samples_total", "tumor_samples", "normal_samples",
    "paired_patients", "survival_samples", "survival_events", "mapped_target_genes",
    "requested_target_genes", "missing_probe_target_genes", "missing_scored_signature_genes", "tac_high_tumor_samples",
    "paired_TMEM158_delta", "paired_TMEM158_FDR",
    "paired_residual_stress_delta", "paired_residual_stress_FDR",
    "paired_ECM_integrin_delta", "paired_ECM_integrin_FDR",
    "TAC_high_residual_stress_delta", "TAC_high_residual_stress_FDR",
    "TAC_high_ECM_integrin_delta", "TAC_high_ECM_integrin_FDR",
    "TMEM158_survival_p", "full_TAC_score_survival_p", "TAC_high_survival_p", "interpretation"
  ),
  value = c(
    "completed", "GSE53625", "GPL18109 sequence-reannotated Agilent array", nrow(scores),
    sum(scores$tissue_group == "Tumor"), sum(scores$tissue_group == "Normal"),
    length(intersect(scores$patient_id[scores$tissue_group == "Tumor"], scores$patient_id[scores$tissue_group == "Normal"])),
    sum(is.finite(tumor_scores$survival_months) & is.finite(tumor_scores$death_event) & tumor_scores$survival_months > 0),
    sum(tumor_scores$death_event == 1, na.rm = TRUE),
    mapped_probe_targets_n, requested_probe_targets_n,
    paste(missing_probe_targets, collapse = ";"),
    paste(setdiff(unique(unlist(gene_sets)), rownames(expr)), collapse = ";"),
    sum(tumor_scores$ecology_subtype == "TAC_high"),
    fmt_num(smim_pair$paired_delta_median), fmt_p(smim_pair$FDR),
    fmt_num(residual_pair$paired_delta_median), fmt_p(residual_pair$FDR),
    fmt_num(ecm_pair$paired_delta_median), fmt_p(ecm_pair$FDR),
    fmt_num(value_or_na(tac_res$delta_high_minus_low[1])), fmt_p(value_or_na(tac_res$FDR[1])),
    fmt_num(value_or_na(tac_ecm$delta_high_minus_low[1])), fmt_p(value_or_na(tac_ecm$FDR[1])),
    fmt_p(value_or_na(tmem_cox$p.value[1])), fmt_p(value_or_na(full_cox$p.value[1])), fmt_p(value_or_na(tac_cox$p.value[1])),
    "Large paired external clinical calibration of TMEM158/TAC-like scores; supports or bounds expression-state reproducibility but does not prove causality or clinical utility."
  )
)
write_csv(status_df, file.path(dirs$qc, "tmem158_gse53625_external_validation_status.csv"))

report <- c(
  "# GSE53625 TMEM158/TAC External Clinical Validation",
  "",
  "## Purpose",
  "",
  "GSE53625 was added as a large external ESCC clinical calibration cohort for the TMEM158-associated TAC_high model. Probe sequences from a representative raw Agilent file were reannotated against GENCODE v19/v36 protein-coding transcripts, reusing the validated GSE53625 route from the earlier SMIM14 branch.",
  "",
  "## Coverage",
  "",
  paste0("- Mapped target genes: ", length(unique(probe_map$gene_symbol)), " of ", length(unique(unlist(gene_sets))), "."),
  paste0("- Probe-map target coverage: ", mapped_probe_targets_n, " of ", requested_probe_targets_n,
         "; missing probe targets: ", ifelse(length(missing_probe_targets), paste(missing_probe_targets, collapse = ", "), "none"), "."),
  paste0("- Scored signature missing genes: ",
         ifelse(nzchar(status_df$value[status_df$item == "missing_scored_signature_genes"]),
                status_df$value[status_df$item == "missing_scored_signature_genes"], "none"), "."),
  "- This is a targeted external clinical calibration layer, not full transcriptome reanalysis.",
  "",
  "## Main Results",
  "",
  paste0("- Samples: ", nrow(scores), " total; ", sum(scores$tissue_group == "Tumor"), " tumours and ", sum(scores$tissue_group == "Normal"), " paired normals."),
  paste0("- TMEM158 paired tumour-normal median delta = ", fmt_num(smim_pair$paired_delta_median), "; FDR=", fmt_p(smim_pair$FDR), "."),
  paste0("- Residual stress score paired delta = ", fmt_num(residual_pair$paired_delta_median), "; FDR=", fmt_p(residual_pair$FDR), "."),
  paste0("- ECM-integrin bridge score paired delta = ", fmt_num(ecm_pair$paired_delta_median), "; FDR=", fmt_p(ecm_pair$FDR), "."),
  paste0("- TAC_high tumours: ", sum(tumor_scores$ecology_subtype == "TAC_high"), " of ", nrow(tumor_scores), "."),
  paste0("- TAC_high vs other residual stress median delta = ", fmt_num(value_or_na(tac_res$delta_high_minus_low[1])), "; FDR=", fmt_p(value_or_na(tac_res$FDR[1])), "."),
  paste0("- TAC_high vs other ECM-integrin bridge median delta = ", fmt_num(value_or_na(tac_ecm$delta_high_minus_low[1])), "; FDR=", fmt_p(value_or_na(tac_ecm$FDR[1])), "."),
  paste0("- Tumour-only TMEM158 Cox P=", fmt_p(value_or_na(tmem_cox$p.value[1])),
         "; full TAC score Cox P=", fmt_p(value_or_na(full_cox$p.value[1])),
         "; TAC_high indicator Cox P=", fmt_p(value_or_na(tac_cox$p.value[1])), "."),
  "",
  "## Interpretation Boundary",
  "",
  "This layer strengthens external clinical calibration because it tests TMEM158/TAC-like scores in an independent 179-pair ESCC cohort with survival annotations. It should be written as public-data external calibration. It must not be described as causal validation, clinical utility, treatment prediction, or definitive prognostic subtype validation.",
  "",
  "## Outputs",
  "",
  "- `05_figures/figure24_gse53625_tmem158_tac_external_validation.*`",
  "- `02_data/processed/tmem158_gse53625_clinical_sample_scores.csv`",
  "- `02_data/processed/tmem158_gse53625_tumor_tac_scores_survival.csv`",
  "- `04_results/validation/tmem158_gse53625_signature_coverage.csv`",
  "- `04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv`",
  "- `04_results/validation/tmem158_gse53625_tac_state_contrasts.csv`",
  "- `04_results/survival/tmem158_gse53625_survival_cox.csv`"
)
writeLines(report, file.path(dirs$manuscript, "tmem158_gse53625_external_clinical_validation_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
base_index <- safe_read_csv(index_path, required = FALSE)
new_index <- data.frame(
  result = c(
    "gse53625_tmem158_probe_gene_map", "gse53625_tmem158_probe_mapping_status",
    "gse53625_tmem158_signature_coverage", "gse53625_tmem158_sample_scores",
    "gse53625_tmem158_tac_scores_survival", "gse53625_tmem158_paired_tests",
    "gse53625_tmem158_tac_state_contrasts", "gse53625_tmem158_survival_cox",
    "gse53625_tmem158_external_validation_status", "figure24_gse53625_tmem158_tac_external_validation",
    "gse53625_tmem158_external_validation_update"
  ),
  path = c(
    "02_data/processed/gse53625_tmem158_probe_gene_map.csv",
    "04_results/qc/tmem158_gse53625_probe_mapping_status.csv",
    "04_results/validation/tmem158_gse53625_signature_coverage.csv",
    "02_data/processed/tmem158_gse53625_clinical_sample_scores.csv",
    "02_data/processed/tmem158_gse53625_tumor_tac_scores_survival.csv",
    "04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv",
    "04_results/validation/tmem158_gse53625_tac_state_contrasts.csv",
    "04_results/survival/tmem158_gse53625_survival_cox.csv",
    "04_results/qc/tmem158_gse53625_external_validation_status.csv",
    "05_figures/figure24_gse53625_tmem158_tac_external_validation.png",
    "07_manuscript/tmem158_gse53625_external_clinical_validation_update.md"
  )
)
if (is.null(base_index)) {
  write_csv(new_index, index_path)
} else {
  base_index <- base_index[!base_index$result %in% new_index$result, ]
  write_csv(rbind(base_index, new_index), index_path)
}

write_log("GSE53625 TMEM158/TAC external validation module completed")
