#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
project_root <- normalizePath(getwd(), mustWork = TRUE)
source_root <- file.path(project_root, "SMIM14_CaUPR_ESCC")
log_file <- file.path(branch_root, "logs", "tmem158_stromal_adjusted_tac_program.log")
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
  (x - mean(x, na.rm = TRUE)) / s
}

read_gmt <- function(path, prefix = NULL) {
  if (!file.exists(path) || file.info(path)$size == 0) return(list())
  lines <- readLines(path, warn = FALSE)
  out <- list()
  for (ln in lines) {
    parts <- strsplit(ln, "\t", fixed = TRUE)[[1]]
    if (length(parts) < 3) next
    nm <- parts[1]
    if (!is.null(prefix)) nm <- paste0(prefix, nm)
    genes <- unique(parts[-c(1, 2)])
    genes <- genes[nzchar(genes)]
    out[[nm]] <- genes
  }
  out
}

signed_stouffer <- function(tab, effect_col = "effect") {
  tab <- tab[is.finite(tab$p.value) & is.finite(tab[[effect_col]]), ]
  if (nrow(tab) == 0) {
    return(data.frame(n_testable = 0, signed_z = NA_real_, meta_p = NA_real_,
                      positive_nominal = 0, negative_nominal = 0))
  }
  p <- pmax(tab$p.value, .Machine$double.xmin)
  z <- stats::qnorm(1 - p / 2) * sign(tab[[effect_col]])
  w <- sqrt(tab$n_total)
  signed_z <- sum(w * z, na.rm = TRUE) / sqrt(sum(w^2, na.rm = TRUE))
  data.frame(
    n_testable = nrow(tab),
    signed_z = signed_z,
    meta_p = 2 * stats::pnorm(-abs(signed_z)),
    positive_nominal = sum(tab$p.value < 0.05 & tab[[effect_col]] > 0, na.rm = TRUE),
    negative_nominal = sum(tab$p.value < 0.05 & tab[[effect_col]] < 0, na.rm = TRUE)
  )
}

signed_stouffer_genes <- function(tab) {
  tab <- tab[is.finite(tab$P.Value) & is.finite(tab$logFC), ]
  if (nrow(tab) == 0) return(NULL)
  split_tab <- split(tab, tab$gene)
  out <- lapply(split_tab, function(d) {
    p <- pmax(d$P.Value, 1e-300)
    z <- stats::qnorm(1 - p / 2) * sign(d$logFC)
    w <- sqrt(d$n_samples)
    combined_z <- sum(w * z, na.rm = TRUE) / sqrt(sum(w^2, na.rm = TRUE))
    data.frame(
      gene = d$gene[1],
      n_datasets = nrow(d),
      combined_z = combined_z,
      meta_p = 2 * stats::pnorm(-abs(combined_z)),
      mean_logFC = mean(d$logFC, na.rm = TRUE),
      median_logFC = stats::median(d$logFC, na.rm = TRUE),
      positive_nominal = sum(d$P.Value < 0.05 & d$logFC > 0, na.rm = TRUE),
      negative_nominal = sum(d$P.Value < 0.05 & d$logFC < 0, na.rm = TRUE),
      positive_fdr = sum(d$adj.P.Val < 0.10 & d$logFC > 0, na.rm = TRUE),
      negative_fdr = sum(d$adj.P.Val < 0.10 & d$logFC < 0, na.rm = TRUE),
      sign_consistency = max(sum(d$logFC > 0, na.rm = TRUE), sum(d$logFC < 0, na.rm = TRUE)) / nrow(d)
    )
  })
  ans <- do.call(rbind, out)
  ans$meta_FDR <- stats::p.adjust(ans$meta_p, method = "BH")
  ans[order(ans$meta_p), ]
}

geneset_enrichment <- function(meta, gene_sets, min_size = 8, max_size = 500) {
  score <- meta$combined_z
  names(score) <- meta$gene
  score <- score[is.finite(score)]
  universe <- names(score)
  out <- lapply(names(gene_sets), function(set_name) {
    present <- intersect(unique(gene_sets[[set_name]]), universe)
    n <- length(present)
    if (n < min_size || n > max_size) return(NULL)
    in_score <- score[present]
    out_score <- score[setdiff(universe, present)]
    if (length(out_score) < min_size) return(NULL)
    p_greater <- suppressWarnings(stats::wilcox.test(in_score, out_score, alternative = "greater")$p.value)
    p_less <- suppressWarnings(stats::wilcox.test(in_score, out_score, alternative = "less")$p.value)
    direction <- ifelse(mean(in_score, na.rm = TRUE) >= mean(out_score, na.rm = TRUE), "positive", "negative")
    p_directional <- ifelse(direction == "positive", p_greater, p_less)
    data.frame(
      model = "TAC_high_adjusted_for_CAF",
      gene_set = set_name,
      n_present = n,
      mean_z_in_set = mean(in_score, na.rm = TRUE),
      mean_z_background = mean(out_score, na.rm = TRUE),
      delta_mean_z = mean(in_score, na.rm = TRUE) - mean(out_score, na.rm = TRUE),
      median_z_in_set = stats::median(in_score, na.rm = TRUE),
      direction = direction,
      p.value = p_directional,
      leading_genes = paste(names(sort(in_score, decreasing = TRUE))[seq_len(min(10, length(in_score)))], collapse = ";")
    )
  })
  ans <- do.call(rbind, out)
  if (is.null(ans) || nrow(ans) == 0) return(data.frame())
  ans$FDR <- stats::p.adjust(ans$p.value, method = "BH")
  ans[order(ans$p.value), ]
}

clean_set_label <- function(x) {
  x <- gsub("^HALLMARK_", "", x)
  x <- gsub("^REACTOME_", "", x)
  x <- gsub("^CUSTOM_", "", x)
  x <- gsub("_", " ", x)
  x <- tools::toTitleCase(tolower(x))
  ifelse(nchar(x) > 58, paste0(substr(x, 1, 55), "..."), x)
}

plot_save <- function(p, stem, width = 8, height = 5) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height)
  TRUE
}

score_contrast <- function(d, metric, group_col, positive_level, negative_level, label) {
  dd <- d[is.finite(d[[metric]]) & d[[group_col]] %in% c(positive_level, negative_level), , drop = FALSE]
  group <- factor(dd[[group_col]], levels = c(negative_level, positive_level))
  n_pos <- sum(group == positive_level)
  n_neg <- sum(group == negative_level)
  p <- NA_real_
  if (n_pos >= 3 && n_neg >= 3) {
    p <- suppressWarnings(stats::wilcox.test(dd[[metric]] ~ group)$p.value)
  }
  med_pos <- ifelse(n_pos > 0, stats::median(dd[[metric]][group == positive_level], na.rm = TRUE), NA_real_)
  med_neg <- ifelse(n_neg > 0, stats::median(dd[[metric]][group == negative_level], na.rm = TRUE), NA_real_)
  data.frame(
    contrast = label,
    n_positive = n_pos,
    n_negative = n_neg,
    n_total = n_pos + n_neg,
    positive_median = med_pos,
    negative_median = med_neg,
    effect = med_pos - med_neg,
    p.value = p
  )
}

write_log("Reading TAC_high states, expression matrix and gene sets")

if (!requireNamespace("limma", quietly = TRUE)) stop("limma package is required")
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("ggplot2 package is required")

state_scores <- read_csv(file.path(branch_root, "02_data", "processed", "tmem158_tumor_ecology_state_scores.csv"))
expr <- readRDS(file.path(source_root, "data", "processed", "tcga_geo_combat_expression_common_genes.rds"))

required <- c("sample", "dataset", "ecology_subtype", "core_axis_state_score", "CAF_score",
              "Proteostasis_score", "Survival_score", "Drug_efflux_score",
              "UPR_composite", "PERK_bias_index", "IRE1_score", "ATF6_score")
missing <- setdiff(required, names(state_scores))
if (length(missing) > 0) stop("Missing required state columns: ", paste(missing, collapse = ", "))

state_scores$tac_high_num <- as.numeric(state_scores$ecology_subtype == "TAC_high")
state_scores$core_high_factor <- ifelse(state_scores$ecology_subtype == "TAC_high", "TAC_high",
                                        ifelse(state_scores$ecology_subtype == "CAF_only", "CAF_only", NA_character_))
state_scores$tac_vs_axis_factor <- ifelse(state_scores$ecology_subtype == "TAC_high", "TAC_high",
                                          ifelse(state_scores$ecology_subtype == "Axis_only", "Axis_only", NA_character_))

score_metrics <- c("Proteostasis_score", "Survival_score", "Drug_efflux_score",
                   "UPR_composite", "PERK_bias_index", "IRE1_score", "ATF6_score")

score_rows <- data.frame()
model_rows <- data.frame()
diagnostics <- data.frame()
adjusted_scores <- state_scores

for (ds in sort(unique(state_scores$dataset))) {
  idx <- which(state_scores$dataset == ds)
  d <- state_scores[idx, , drop = FALSE]
  d$z_CAF_score <- zscore(d$CAF_score)
  d$z_core_axis_state_score <- zscore(d$core_axis_state_score)
  r <- suppressWarnings(stats::cor(d$tac_high_num, d$z_CAF_score, method = "spearman", use = "pairwise.complete.obs"))
  vif <- ifelse(is.finite(r) && abs(r) < 1, 1 / (1 - r^2), NA_real_)
  diagnostics <- rbind(diagnostics, data.frame(
    dataset = ds,
    n_samples = nrow(d),
    n_TAC_high = sum(d$ecology_subtype == "TAC_high"),
    n_CAF_only = sum(d$ecology_subtype == "CAF_only"),
    n_Axis_only = sum(d$ecology_subtype == "Axis_only"),
    tac_high_caf_spearman = r,
    tac_high_caf_vif_approx = vif
  ))

  for (metric in score_metrics) {
    z_metric <- paste0("z_", metric)
    residual_metric <- paste0("CAF_adjusted_", metric)
    d[[z_metric]] <- zscore(d[[metric]])
    fit_resid <- stats::lm(d[[z_metric]] ~ d$z_CAF_score)
    d[[residual_metric]] <- stats::residuals(fit_resid)
    adjusted_scores[idx, residual_metric] <- d[[residual_metric]]

    tmp <- score_contrast(d, residual_metric, "ecology_subtype", "TAC_high", "TAC_low",
                          "TAC_high_vs_TAC_low_CAF_adjusted")
    score_rows <- rbind(score_rows, cbind(dataset = ds, metric = metric, tmp))

    tmp <- score_contrast(d, residual_metric, "core_high_factor", "TAC_high", "CAF_only",
                          "TAC_high_vs_CAF_only_CAF_adjusted")
    score_rows <- rbind(score_rows, cbind(dataset = ds, metric = metric, tmp))

    tmp <- score_contrast(d, residual_metric, "tac_vs_axis_factor", "TAC_high", "Axis_only",
                          "TAC_high_vs_Axis_only_CAF_adjusted")
    score_rows <- rbind(score_rows, cbind(dataset = ds, metric = metric, tmp))

    fit_core <- stats::lm(d[[z_metric]] ~ d$z_core_axis_state_score + d$z_CAF_score)
    coef_core <- summary(fit_core)$coefficients
    core_term <- "d$z_core_axis_state_score"
    model_rows <- rbind(model_rows, data.frame(
      dataset = ds,
      metric = metric,
      model = "score_z_on_core_axis_plus_CAF",
      term = "core_axis_state_score_adjusted_for_CAF",
      n_total = nrow(d),
      effect = ifelse(core_term %in% rownames(coef_core), coef_core[core_term, "Estimate"], NA_real_),
      p.value = ifelse(core_term %in% rownames(coef_core), coef_core[core_term, "Pr(>|t|)"], NA_real_),
      adj_r2 = summary(fit_core)$adj.r.squared
    ))

    fit_tac <- stats::lm(d[[z_metric]] ~ d$tac_high_num + d$z_CAF_score)
    coef_tac <- summary(fit_tac)$coefficients
    tac_term <- "d$tac_high_num"
    model_rows <- rbind(model_rows, data.frame(
      dataset = ds,
      metric = metric,
      model = "score_z_on_TAC_high_plus_CAF",
      term = "TAC_high_adjusted_for_CAF",
      n_total = nrow(d),
      effect = ifelse(tac_term %in% rownames(coef_tac), coef_tac[tac_term, "Estimate"], NA_real_),
      p.value = ifelse(tac_term %in% rownames(coef_tac), coef_tac[tac_term, "Pr(>|t|)"], NA_real_),
      adj_r2 = summary(fit_tac)$adj.r.squared
    ))
  }
}

score_rows$FDR <- stats::p.adjust(score_rows$p.value, method = "BH")
score_rows$direction <- ifelse(score_rows$effect > 0, "higher_in_TAC_high", "lower_in_TAC_high")
write_csv(score_rows, file.path(branch_root, "04_results", "validation", "tmem158_stromal_adjusted_score_contrasts.csv"))

model_rows$FDR <- stats::p.adjust(model_rows$p.value, method = "BH")
write_csv(model_rows, file.path(branch_root, "04_results", "validation", "tmem158_stromal_adjusted_score_models.csv"))
write_csv(diagnostics, file.path(branch_root, "04_results", "validation", "tmem158_stromal_adjustment_collinearity_diagnostics.csv"))
write_csv(adjusted_scores, file.path(branch_root, "02_data", "processed", "tmem158_tumor_ecology_state_scores_caf_adjusted.csv"))

score_meta <- do.call(rbind, lapply(split(score_rows, paste(score_rows$metric, score_rows$contrast, sep = "||")), function(tab) {
  ans <- signed_stouffer(tab)
  parts <- strsplit(unique(paste(tab$metric, tab$contrast, sep = "||")), "\\|\\|")[[1]]
  data.frame(metric = parts[1], contrast = parts[2], ans)
}))
score_meta$meta_FDR <- stats::p.adjust(score_meta$meta_p, method = "BH")
score_meta$replication_call <- ifelse(score_meta$meta_FDR < 0.10 & score_meta$signed_z > 0 & score_meta$positive_nominal >= 2,
                                      "CAF_adjusted_replicated_positive",
                                      ifelse(score_meta$meta_p < 0.05 & score_meta$signed_z > 0,
                                             "CAF_adjusted_meta_positive_boundary",
                                             ifelse(score_meta$negative_nominal >= 2,
                                                    "CAF_adjusted_negative_or_inconsistent", "not_replicated")))
write_csv(score_meta, file.path(branch_root, "04_results", "validation", "tmem158_stromal_adjusted_score_meta.csv"))

model_meta <- do.call(rbind, lapply(split(model_rows, paste(model_rows$metric, model_rows$term, sep = "||")), function(tab) {
  ans <- signed_stouffer(tab)
  parts <- strsplit(unique(paste(tab$metric, tab$term, sep = "||")), "\\|\\|")[[1]]
  data.frame(metric = parts[1], term = parts[2], ans)
}))
model_meta$meta_FDR <- stats::p.adjust(model_meta$meta_p, method = "BH")
model_meta$replication_call <- ifelse(model_meta$meta_FDR < 0.10 & model_meta$signed_z > 0 & model_meta$positive_nominal >= 2,
                                      "CAF_adjusted_replicated_positive",
                                      ifelse(model_meta$meta_p < 0.05 & model_meta$signed_z > 0,
                                             "CAF_adjusted_meta_positive_boundary",
                                             ifelse(model_meta$negative_nominal >= 2,
                                                    "CAF_adjusted_negative_or_inconsistent", "not_replicated")))
write_csv(model_meta, file.path(branch_root, "04_results", "validation", "tmem158_stromal_adjusted_score_model_meta.csv"))

custom_sets <- list(
  CUSTOM_DRUG_EFFLUX_TRANSPORT = c("ABCB1", "ABCB8", "ABCC1", "ABCC2", "ABCC3", "ABCC4", "ABCG2", "ATP7A", "ATP7B", "SLC31A1"),
  CUSTOM_ER_PROTEOSTASIS = c("HSPA5", "HSP90B1", "PDIA4", "DNAJB9", "HERPUD1", "CALR", "CANX", "EDEM1", "SEL1L", "VCP", "DERL1", "DERL2", "DERL3"),
  CUSTOM_UPR_PERK = c("EIF2AK3", "ATF4", "DDIT3", "PPP1R15A", "DNAJC3", "TRIB3", "ASNS", "SLC7A11"),
  CUSTOM_UPR_IRE1 = c("ERN1", "XBP1", "HSPA5", "DNAJB9", "HERPUD1", "EDEM1"),
  CUSTOM_UPR_ATF6 = c("ATF6", "HSPA5", "HSP90B1", "PDIA4", "CALR", "CANX", "SEL1L"),
  CUSTOM_CAF_ECM = c("ACTA2", "FAP", "COL1A1", "COL1A2", "COL3A1", "COL5A1", "COL6A1", "DCN", "PDPN", "TAGLN", "THY1", "CXCL12"),
  CUSTOM_PROTEIN_BIOGENESIS = c("RPLP0", "RPL3", "RPL4", "RPL5", "RPS3", "RPS6", "SRP14", "SRP54", "SSR1", "SEC61A1", "SEC61B", "DDOST", "RPN1", "RPN2"),
  CUSTOM_OXPHOS_MYC_TRANSLATION = c("MYC", "NDUFA1", "NDUFA2", "NDUFB5", "NDUFS1", "COX5A", "COX6A1", "ATP5F1A", "ATP5F1B", "EIF4A1", "EIF4E", "EIF2S1")
)
hallmark_sets <- read_gmt(file.path(source_root, "data", "external", "msigdb_hallmark_symbols.gmt"))
reactome_sets <- read_gmt(file.path(source_root, "data", "external", "msigdb_reactome_symbols.gmt"))
gene_sets <- c(custom_sets, hallmark_sets, reactome_sets)

common_samples <- intersect(state_scores$sample, colnames(expr))
if (length(common_samples) < 50) stop("Too few matched expression/state samples")
state_expr <- state_scores[match(common_samples, state_scores$sample), , drop = FALSE]
expr <- expr[, common_samples, drop = FALSE]

per_cohort <- data.frame()
model_status <- data.frame()

for (ds in sort(unique(state_expr$dataset))) {
  idx <- which(state_expr$dataset == ds)
  d <- state_expr[idx, , drop = FALSE]
  e <- expr[, idx, drop = FALSE]
  d$z_CAF_score <- zscore(d$CAF_score)
  d$tac_high_num <- as.numeric(d$ecology_subtype == "TAC_high")
  n_tac <- sum(d$tac_high_num == 1, na.rm = TRUE)
  n_other <- sum(d$tac_high_num == 0, na.rm = TRUE)
  design <- stats::model.matrix(~ z_CAF_score + tac_high_num, data = d)
  if (n_tac < 3 || n_other < 3 || qr(design)$rank < ncol(design)) {
    model_status <- rbind(model_status, data.frame(
      model = "TAC_high_adjusted_for_CAF",
      dataset = ds,
      status = "skipped_small_or_collinear",
      n_samples = nrow(d),
      n_TAC_high = n_tac,
      n_other = n_other
    ))
    next
  }
  fit <- limma::eBayes(limma::lmFit(e, design))
  tt <- limma::topTable(fit, coef = "tac_high_num", number = Inf, sort.by = "none")
  tt$gene <- rownames(tt)
  tt$dataset <- ds
  tt$model <- "TAC_high_adjusted_for_CAF"
  tt$n_samples <- nrow(d)
  tt$n_high <- n_tac
  tt$n_low <- n_other
  per_cohort <- rbind(per_cohort, tt[, c("model", "dataset", "gene", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "n_samples", "n_high", "n_low")])
  model_status <- rbind(model_status, data.frame(
    model = "TAC_high_adjusted_for_CAF",
    dataset = ds,
    status = "completed",
    n_samples = nrow(d),
    n_TAC_high = n_tac,
    n_other = n_other
  ))
}

write_csv(per_cohort, file.path(branch_root, "04_results", "transcriptome", "tmem158_stromal_adjusted_per_cohort_limma.csv"))
write_csv(model_status, file.path(branch_root, "04_results", "qc", "tmem158_stromal_adjusted_model_status.csv"))

meta <- signed_stouffer_genes(per_cohort)
if (is.null(meta)) meta <- data.frame()
if (nrow(meta) > 0) {
  meta$model <- "TAC_high_adjusted_for_CAF"
  meta <- meta[, c("model", setdiff(names(meta), "model"))]
}
write_csv(meta, file.path(branch_root, "04_results", "transcriptome", "tmem158_stromal_adjusted_meta_differential_genes.csv"))

enrichment <- if (nrow(meta) > 0) geneset_enrichment(meta, gene_sets) else data.frame()
write_csv(enrichment, file.path(branch_root, "04_results", "transcriptome", "tmem158_stromal_adjusted_geneset_enrichment.csv"))

top_genes <- if (nrow(meta) > 0) head(meta[order(meta$meta_p), ], 250) else data.frame()
write_csv(top_genes, file.path(branch_root, "04_results", "transcriptome", "tmem158_stromal_adjusted_top_meta_genes.csv"))

get_meta_value <- function(tab, metric, contrast_or_term, value_col, mode = c("contrast", "term")) {
  mode <- match.arg(mode)
  if (nrow(tab) == 0) return(NA_real_)
  key_col <- ifelse(mode == "contrast", "contrast", "term")
  idx <- which(tab$metric == metric & tab[[key_col]] == contrast_or_term)
  if (length(idx) == 0) return(NA_real_)
  tab[idx[1], value_col]
}

pathway_lookup <- function(set_name, col) {
  if (nrow(enrichment) == 0 || !(set_name %in% enrichment$gene_set)) return(NA_real_)
  enrichment[match(set_name, enrichment$gene_set), col]
}

status <- data.frame(
  item = c(
    "module_status", "bulk_datasets", "expression_matched_genes", "expression_matched_tumor_samples",
    "caf_adjusted_limma_completed_cohorts",
    "caf_adjusted_positive_genes_meta_FDR_0.10",
    "caf_adjusted_negative_genes_meta_FDR_0.10",
    "top_caf_adjusted_gene",
    "top_caf_adjusted_positive_gene",
    "top_caf_adjusted_pathway",
    "custom_er_proteostasis_FDR",
    "custom_drug_efflux_transport_FDR",
    "custom_caf_ecm_FDR",
    "score_TAC_vs_CAF_only_proteostasis_meta_FDR",
    "score_TAC_vs_CAF_only_drug_efflux_meta_FDR",
    "core_axis_adjusted_for_CAF_proteostasis_meta_FDR",
    "core_axis_adjusted_for_CAF_drug_efflux_meta_FDR",
    "interpretation"
  ),
  value = c(
    "completed",
    length(unique(state_scores$dataset)),
    nrow(expr),
    ncol(expr),
    sum(model_status$status == "completed"),
    ifelse(nrow(meta) > 0, sum(meta$meta_FDR < 0.10 & meta$combined_z > 0, na.rm = TRUE), 0),
    ifelse(nrow(meta) > 0, sum(meta$meta_FDR < 0.10 & meta$combined_z < 0, na.rm = TRUE), 0),
    ifelse(nrow(meta) > 0, meta$gene[which.min(meta$meta_p)], NA_character_),
    ifelse(nrow(meta[meta$combined_z > 0, , drop = FALSE]) > 0, meta$gene[which(meta$combined_z > 0)[1]], NA_character_),
    ifelse(nrow(enrichment) > 0, enrichment$gene_set[which.min(enrichment$p.value)], NA_character_),
    pathway_lookup("CUSTOM_ER_PROTEOSTASIS", "FDR"),
    pathway_lookup("CUSTOM_DRUG_EFFLUX_TRANSPORT", "FDR"),
    pathway_lookup("CUSTOM_CAF_ECM", "FDR"),
    get_meta_value(score_meta, "Proteostasis_score", "TAC_high_vs_CAF_only_CAF_adjusted", "meta_FDR", "contrast"),
    get_meta_value(score_meta, "Drug_efflux_score", "TAC_high_vs_CAF_only_CAF_adjusted", "meta_FDR", "contrast"),
    get_meta_value(model_meta, "Proteostasis_score", "core_axis_state_score_adjusted_for_CAF", "meta_FDR", "term"),
    get_meta_value(model_meta, "Drug_efflux_score", "core_axis_state_score_adjusted_for_CAF", "meta_FDR", "term"),
    "CAF/stromal adjustment tests whether TAC_high retains axis-linked signal beyond continuous CAF abundance; association only"
  )
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_stromal_adjusted_tac_program_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)

  pdat <- score_meta[score_meta$metric %in% c("Proteostasis_score", "Drug_efflux_score", "Survival_score", "UPR_composite") &
                       score_meta$contrast %in% c("TAC_high_vs_CAF_only_CAF_adjusted", "TAC_high_vs_Axis_only_CAF_adjusted"), , drop = FALSE]
  if (nrow(pdat) > 0) {
    pdat$metric_label <- gsub("_score", "", pdat$metric)
    pdat$metric_label <- gsub("_", " ", pdat$metric_label)
    pdat$contrast_label <- ifelse(pdat$contrast == "TAC_high_vs_CAF_only_CAF_adjusted",
                                  "TAC high vs CAF only", "TAC high vs Axis only")
    p <- ggplot(pdat, aes(x = metric_label, y = signed_z, fill = contrast_label)) +
      geom_hline(yintercept = 0, linewidth = 0.35, colour = "grey55") +
      geom_col(position = position_dodge(width = 0.72), width = 0.62, colour = "grey25", linewidth = 0.2) +
      geom_text(aes(label = paste0("FDR=", signif(meta_FDR, 2))),
                position = position_dodge(width = 0.72), vjust = ifelse(pdat$signed_z >= 0, -0.45, 1.2), size = 2.7) +
      scale_fill_manual(values = c("TAC high vs CAF only" = "#2a6f97", "TAC high vs Axis only" = "#b5651d")) +
      labs(
        title = "CAF-adjusted TAC_high score specificity",
        x = NULL,
        y = "Signed meta-z after continuous CAF adjustment",
        fill = NULL
      ) +
      theme_bw(base_size = 10) +
      theme(
        plot.title = element_text(face = "bold", size = 12.5),
        axis.text.x = element_text(angle = 25, hjust = 1),
        panel.grid.minor = element_blank(),
        legend.position = "top"
      )
    plot_save(p, file.path(branch_root, "05_figures", "figure22_stromal_adjusted_tac_score_specificity"), width = 8.2, height = 4.8)
  }

  edat <- enrichment[enrichment$direction == "positive" & is.finite(enrichment$FDR), , drop = FALSE]
  edat <- edat[order(edat$FDR, -edat$delta_mean_z), , drop = FALSE]
  edat <- head(edat, 14)
  if (nrow(edat) > 0) {
    edat$label <- clean_set_label(edat$gene_set)
    edat$minus_log10_FDR <- -log10(pmax(edat$FDR, 1e-300))
    edat$label <- factor(edat$label, levels = rev(edat$label))
    p2 <- ggplot(edat, aes(x = label, y = minus_log10_FDR, fill = delta_mean_z)) +
      geom_col(width = 0.68, colour = "grey25", linewidth = 0.15) +
      coord_flip() +
      scale_fill_gradient2(low = "#6b8fb3", mid = "#f4f0e6", high = "#b65f3a", midpoint = 0) +
      labs(
        title = "CAF-adjusted TAC_high transcriptome pathways",
        x = NULL,
        y = "-log10(FDR)",
        fill = "Mean z delta"
      ) +
      theme_bw(base_size = 10) +
      theme(
        plot.title = element_text(face = "bold", size = 12.5),
        panel.grid.minor = element_blank(),
        legend.position = "right"
      )
    plot_save(p2, file.path(branch_root, "05_figures", "figure23_stromal_adjusted_tac_transcriptome"), width = 8.4, height = 5.4)
  }
}

fmt <- function(x) {
  if (length(x) == 0 || is.na(x) || !is.finite(as.numeric(x))) return("NA")
  signif(as.numeric(x), 4)
}

status_value <- function(item) {
  status$value[match(item, status$item)]
}

report <- c(
  "# CAF-adjusted TAC_high Programme Update",
  "",
  "This module tests whether the TAC_high programme is fully explained by continuous CAF abundance or whether axis-linked residual signals remain after stromal adjustment.",
  "",
  "## Outputs",
  "",
  "- `04_results/validation/tmem158_stromal_adjusted_score_contrasts.csv`",
  "- `04_results/validation/tmem158_stromal_adjusted_score_meta.csv`",
  "- `04_results/validation/tmem158_stromal_adjusted_score_models.csv`",
  "- `04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv`",
  "- `04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv`",
  "- `05_figures/figure22_stromal_adjusted_tac_score_specificity.*`",
  "- `05_figures/figure23_stromal_adjusted_tac_transcriptome.*`",
  "",
  "## Key Interpretation",
  "",
  sprintf("The CAF-adjusted limma model completed in %s cohorts and tested %s genes across %s tumour samples.",
          status_value("caf_adjusted_limma_completed_cohorts"),
          status_value("expression_matched_genes"),
          status_value("expression_matched_tumor_samples")),
  "",
  sprintf("After adjustment for continuous CAF score, the transcriptome layer detected %s positive and %s negative meta-FDR<0.10 genes. The top overall CAF-adjusted gene was `%s`, and the top positive gene was `%s`.",
          status_value("caf_adjusted_positive_genes_meta_FDR_0.10"),
          status_value("caf_adjusted_negative_genes_meta_FDR_0.10"),
          status_value("top_caf_adjusted_gene"),
          status_value("top_caf_adjusted_positive_gene")),
  "",
  sprintf("Custom ER proteostasis FDR=%s, drug-efflux/transport FDR=%s, and CAF/ECM FDR=%s after CAF adjustment.",
          fmt(status_value("custom_er_proteostasis_FDR")),
          fmt(status_value("custom_drug_efflux_transport_FDR")),
          fmt(status_value("custom_caf_ecm_FDR"))),
  "",
  sprintf("At the score level, TAC_high vs CAF_only after CAF residualization showed Proteostasis meta-FDR=%s and Drug-efflux meta-FDR=%s.",
          fmt(status_value("score_TAC_vs_CAF_only_proteostasis_meta_FDR")),
          fmt(status_value("score_TAC_vs_CAF_only_drug_efflux_meta_FDR"))),
  "",
  sprintf("Continuous core-axis effects adjusted for CAF showed Proteostasis meta-FDR=%s and Drug-efflux meta-FDR=%s.",
          fmt(status_value("core_axis_adjusted_for_CAF_proteostasis_meta_FDR")),
          fmt(status_value("core_axis_adjusted_for_CAF_drug_efflux_meta_FDR"))),
  "",
  "This layer should be written as a stromal-confounding stress test. It can support a CAF-coupled axis-state interpretation if residual signals remain, but it cannot prove tumour-cell-intrinsic causality."
)
writeLines(report, con = file.path(branch_root, "07_manuscript", "tmem158_stromal_adjusted_tac_program_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
new_index <- data.frame(
  result = c(
    "stromal_adjusted_tac_status",
    "stromal_adjusted_score_meta",
    "stromal_adjusted_score_model_meta",
    "stromal_adjusted_meta_differential_genes",
    "stromal_adjusted_geneset_enrichment",
    "figure22_stromal_adjusted_tac_score_specificity",
    "figure23_stromal_adjusted_tac_transcriptome",
    "stromal_adjusted_tac_program_update"
  ),
  path = c(
    "04_results/qc/tmem158_stromal_adjusted_tac_program_status.csv",
    "04_results/validation/tmem158_stromal_adjusted_score_meta.csv",
    "04_results/validation/tmem158_stromal_adjusted_score_model_meta.csv",
    "04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv",
    "04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv",
    "05_figures/figure22_stromal_adjusted_tac_score_specificity.png",
    "05_figures/figure23_stromal_adjusted_tac_transcriptome.png",
    "07_manuscript/tmem158_stromal_adjusted_tac_program_update.md"
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

write_log("CAF-adjusted TAC_high programme module completed")
