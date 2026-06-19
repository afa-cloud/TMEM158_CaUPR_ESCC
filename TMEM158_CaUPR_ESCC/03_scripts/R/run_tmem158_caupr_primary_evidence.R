#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
project_root <- normalizePath(getwd(), mustWork = TRUE)
source_root <- file.path(project_root, "SMIM14_CaUPR_ESCC")
screen_root <- file.path(project_root, "CaUPR_CAF_Regulator_ESCC")
decision_root <- file.path(project_root, "CaUPR_Regulator_FinalDecision_ESCC")

log_file <- file.path(branch_root, "logs", "tmem158_primary_evidence.log")
dir.create(dirname(log_file), showWarnings = FALSE, recursive = TRUE)

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

gene_score <- function(expr, genes) {
  genes <- intersect(genes, rownames(expr))
  if (length(genes) == 0) return(rep(NA_real_, ncol(expr)))
  m <- expr[genes, , drop = FALSE]
  if (nrow(m) == 1) return(zscore(as.numeric(m[1, ])))
  colMeans(t(apply(m, 1, zscore)), na.rm = TRUE)
}

spearman_row <- function(data, x, y, label = NULL) {
  ok <- is.finite(data[[x]]) & is.finite(data[[y]])
  n <- sum(ok)
  if (n < 5) {
    return(data.frame(metric = ifelse(is.null(label), y, label), n = n,
                      rho = NA_real_, p.value = NA_real_))
  }
  ct <- suppressWarnings(stats::cor.test(data[[x]][ok], data[[y]][ok], method = "spearman"))
  data.frame(metric = ifelse(is.null(label), y, label), n = n,
             rho = unname(ct$estimate), p.value = ct$p.value)
}

wilcox_row <- function(data, value_col, group_col, dataset) {
  d <- data[is.finite(data[[value_col]]) & data[[group_col]] %in% c("Tumor", "Normal"), ]
  n_t <- sum(d[[group_col]] == "Tumor")
  n_n <- sum(d[[group_col]] == "Normal")
  if (n_t < 3 || n_n < 3) {
    p <- NA_real_
  } else {
    p <- suppressWarnings(stats::wilcox.test(d[[value_col]] ~ d[[group_col]])$p.value)
  }
  data.frame(
    dataset = dataset,
    metric = value_col,
    n_tumor = n_t,
    n_normal = n_n,
    tumor_median = ifelse(n_t > 0, stats::median(d[[value_col]][d[[group_col]] == "Tumor"], na.rm = TRUE), NA_real_),
    normal_median = ifelse(n_n > 0, stats::median(d[[value_col]][d[[group_col]] == "Normal"], na.rm = TRUE), NA_real_),
    delta_tumor_minus_normal = ifelse(n_t > 0 && n_n > 0,
                                      stats::median(d[[value_col]][d[[group_col]] == "Tumor"], na.rm = TRUE) -
                                        stats::median(d[[value_col]][d[[group_col]] == "Normal"], na.rm = TRUE),
                                      NA_real_),
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

write_log("Reading processed matrices and prior evidence")

combat_expr <- readRDS(file.path(source_root, "data", "processed", "tcga_geo_combat_expression_common_genes.rds"))
sample_manifest <- safe_read_csv(file.path(source_root, "results", "tables", "tcga_geo_combat_sample_manifest.csv"))
tcga_expr <- readRDS(file.path(source_root, "data", "processed", "tcga_esca_expression_symbol_log2.rds"))
tcga_clin <- safe_read_csv(file.path(source_root, "data", "processed", "tcga_escc_clinical_survival.csv"))
decision_scores <- safe_read_csv(file.path(decision_root, "06_tables", "candidate_decision_scores.csv"))
literature_counts <- safe_read_csv(file.path(decision_root, "06_tables", "candidate_literature_audit_counts.csv"))
pubmed_top <- safe_read_csv(file.path(decision_root, "06_tables", "candidate_pubmed_top_records.csv"))
gse45670_candidate <- safe_read_csv(file.path(screen_root, "06_tables", "gse45670_candidate_validation.csv"))
scrna_candidate <- safe_read_csv(file.path(screen_root, "06_tables", "gse160269_epithelial_candidate_validation.csv"))
depmap_candidate <- safe_read_csv(file.path(screen_root, "06_tables", "depmap_candidate_validation.csv"))
proteomics_candidate <- safe_read_csv(file.path(screen_root, "06_tables", "proteogenomics_candidate_context_scored.csv"))
scrna_epithelial <- safe_read_csv(file.path(screen_root, "06_tables", "gse160269_candidate_epithelial_pseudobulk.csv"), required = FALSE)
scrna_ecosystem <- safe_read_csv(file.path(source_root, "results", "tables", "scrna_gse160269_ecosystem_merged_tumor_scores.csv"), required = FALSE)

if (!"TMEM158" %in% rownames(combat_expr)) stop("TMEM158 not found in combat expression matrix")
if (!"TMEM158" %in% rownames(tcga_expr)) stop("TMEM158 not found in TCGA expression matrix")

gene_sets <- list(
  Ca2_axis_score = c("STIM1", "ORAI1", "ATP2A2", "ITPR1", "ITPR2", "ITPR3"),
  PERK_score = c("EIF2AK3", "ATF4", "DDIT3"),
  IRE1_score = c("ERN1", "XBP1"),
  ATF6_score = c("ATF6"),
  CAF_score = c("ACTA2", "FAP", "COL1A1", "COL1A2", "CXCL12", "TAGLN", "PDPN", "DCN"),
  Proteostasis_score = c("HSPA5", "HSP90B1", "PDIA4", "DNAJB9", "HERPUD1"),
  Survival_score = c("BIRC5", "BCL2", "BCL2L1", "MCL1"),
  Drug_efflux_score = c("ABCC1", "ABCB1", "ABCG2")
)

coverage <- data.frame(
  signature = names(gene_sets),
  requested_genes = vapply(gene_sets, function(g) paste(g, collapse = ";"), character(1)),
  detected_genes = vapply(gene_sets, function(g) paste(intersect(g, rownames(combat_expr)), collapse = ";"), character(1)),
  n_requested = vapply(gene_sets, length, integer(1)),
  n_detected = vapply(gene_sets, function(g) length(intersect(g, rownames(combat_expr))), integer(1))
)
write_csv(coverage, file.path(branch_root, "02_data", "metadata", "signature_gene_coverage.csv"))

sample_scores <- sample_manifest
sample_scores$TMEM158 <- as.numeric(combat_expr["TMEM158", sample_scores$sample])
for (nm in names(gene_sets)) sample_scores[[nm]] <- gene_score(combat_expr[, sample_scores$sample, drop = FALSE], gene_sets[[nm]])
sample_scores$UPR_composite <- rowMeans(sample_scores[, c("PERK_score", "IRE1_score", "ATF6_score")], na.rm = TRUE)
sample_scores$PERK_bias_index <- sample_scores$PERK_score - rowMeans(sample_scores[, c("IRE1_score", "ATF6_score")], na.rm = TRUE)
sample_scores$TMEM158_group <- ifelse(sample_scores$TMEM158 >= stats::median(sample_scores$TMEM158, na.rm = TRUE), "High", "Low")
write_csv(sample_scores, file.path(branch_root, "02_data", "processed", "tmem158_combat_dataset_sample_scores.csv"))

expr_tests <- do.call(rbind, lapply(split(sample_scores, sample_scores$batch), function(d) wilcox_row(d, "TMEM158", "group", unique(d$batch))))
expr_tests$FDR <- stats::p.adjust(expr_tests$p.value, method = "BH")
write_csv(expr_tests, file.path(branch_root, "04_results", "expression", "tmem158_tumor_normal_tests.csv"))

tumor_cor <- do.call(rbind, lapply(split(sample_scores[sample_scores$group == "Tumor", ], sample_scores$batch[sample_scores$group == "Tumor"]), function(d) {
  out <- do.call(rbind, lapply(c("Ca2_axis_score", "PERK_score", "IRE1_score", "ATF6_score",
                                 "UPR_composite", "PERK_bias_index", "CAF_score",
                                 "Proteostasis_score", "Survival_score", "Drug_efflux_score"),
                               function(y) spearman_row(d, "TMEM158", y)))
  out$dataset <- unique(d$batch)
  out
}))
tumor_cor$FDR <- ave(tumor_cor$p.value, tumor_cor$dataset, FUN = function(p) stats::p.adjust(p, "BH"))
tumor_cor <- tumor_cor[, c("dataset", "metric", "n", "rho", "p.value", "FDR")]
write_csv(tumor_cor, file.path(branch_root, "04_results", "enrichment", "tmem158_axis_correlations_by_dataset.csv"))

tcga_manifest <- sample_manifest[sample_manifest$batch == "TCGA" & sample_manifest$group == "Tumor", ]
tcga_samples <- intersect(tcga_manifest$sample, colnames(tcga_expr))
tcga_scores <- data.frame(sample = tcga_samples, TMEM158 = as.numeric(tcga_expr["TMEM158", tcga_samples]))
for (nm in names(gene_sets)) tcga_scores[[nm]] <- gene_score(tcga_expr[, tcga_samples, drop = FALSE], gene_sets[[nm]])
tcga_scores$UPR_composite <- rowMeans(tcga_scores[, c("PERK_score", "IRE1_score", "ATF6_score")], na.rm = TRUE)
tcga_scores$PERK_bias_index <- tcga_scores$PERK_score - rowMeans(tcga_scores[, c("IRE1_score", "ATF6_score")], na.rm = TRUE)
tcga_scores$patient <- substr(tcga_scores$sample, 1, 12)
tcga_surv <- merge(tcga_scores, tcga_clin, by = c("sample", "patient"), all.x = TRUE)
tcga_surv$TMEM158_group <- ifelse(tcga_surv$TMEM158 >= stats::median(tcga_surv$TMEM158, na.rm = TRUE), "High", "Low")
write_csv(tcga_surv, file.path(branch_root, "02_data", "processed", "tmem158_tcga_tumor_scores_survival.csv"))

surv_rows <- data.frame(model = character(), n = integer(), events = integer(), term = character(),
                        HR = numeric(), p.value = numeric(), note = character())
if (requireNamespace("survival", quietly = TRUE)) {
  d <- tcga_surv[is.finite(tcga_surv$OS.time) & is.finite(tcga_surv$OS) & is.finite(tcga_surv$TMEM158), ]
  if (nrow(d) >= 30 && sum(d$OS == 1) >= 10) {
    fit1 <- survival::coxph(survival::Surv(OS.time, OS) ~ scale(TMEM158), data = d)
    s1 <- summary(fit1)
    surv_rows <- rbind(surv_rows, data.frame(model = "continuous_cox", n = nrow(d), events = sum(d$OS == 1),
                                             term = "scale(TMEM158)",
                                             HR = unname(s1$coefficients[1, "exp(coef)"]),
                                             p.value = unname(s1$coefficients[1, "Pr(>|z|)"]),
                                             note = "TCGA tumour samples"))
    fit2 <- survival::coxph(survival::Surv(OS.time, OS) ~ TMEM158_group, data = d)
    s2 <- summary(fit2)
    surv_rows <- rbind(surv_rows, data.frame(model = "median_group_cox", n = nrow(d), events = sum(d$OS == 1),
                                             term = rownames(s2$coefficients)[1],
                                             HR = unname(s2$coefficients[1, "exp(coef)"]),
                                             p.value = unname(s2$coefficients[1, "Pr(>|z|)"]),
                                             note = "Median high vs low"))
    if ("age" %in% names(d) && sum(is.finite(d$age)) >= 30) {
      fit3 <- survival::coxph(survival::Surv(OS.time, OS) ~ scale(TMEM158) + age, data = d)
      s3 <- summary(fit3)
      surv_rows <- rbind(surv_rows, data.frame(model = "age_adjusted_cox", n = nrow(model.frame(fit3)), events = sum(d$OS == 1, na.rm = TRUE),
                                               term = "scale(TMEM158)",
                                               HR = unname(s3$coefficients["scale(TMEM158)", "exp(coef)"]),
                                               p.value = unname(s3$coefficients["scale(TMEM158)", "Pr(>|z|)"]),
                                               note = "Adjusted for age"))
    }
  }
} else {
  surv_rows <- rbind(surv_rows, data.frame(model = "not_run", n = nrow(tcga_surv), events = sum(tcga_surv$OS == 1, na.rm = TRUE),
                                           term = "survival_package_missing", HR = NA_real_, p.value = NA_real_,
                                           note = "Install survival package to rerun"))
}
surv_rows$FDR <- stats::p.adjust(surv_rows$p.value, method = "BH")
write_csv(surv_rows, file.path(branch_root, "04_results", "survival", "tmem158_tcga_survival.csv"))

scrna_rows <- data.frame(metric = character(), n = integer(), rho = numeric(), p.value = numeric(), source = character())
if (!is.null(scrna_epithelial) && !is.null(scrna_ecosystem) && all(c("sample", "TMEM158") %in% names(scrna_epithelial))) {
  epi <- scrna_epithelial[, c("sample", "condition", "n_cells", "TMEM158", "TMEM158_pct_positive")]
  eco <- scrna_ecosystem
  scrna <- merge(epi, eco, by = "sample")
  for (m in c("CAF_score", "Tcell_exhaustion_score", "Tcell_cytotoxic_score", "Treg_score", "Myeloid_suppressive_score")) {
    if (m %in% names(scrna)) {
      r <- spearman_row(scrna, "TMEM158", m)
      r$source <- "GSE160269 epithelial-to-ecosystem pseudo-bulk"
      scrna_rows <- rbind(scrna_rows, r)
    }
  }
  scrna_rows$FDR <- stats::p.adjust(scrna_rows$p.value, method = "BH")
  write_csv(scrna, file.path(branch_root, "02_data", "processed", "tmem158_gse160269_epithelial_ecosystem_scores.csv"))
}
write_csv(scrna_rows, file.path(branch_root, "04_results", "immune", "tmem158_scrna_ecosystem_correlations.csv"))

tm_decision <- decision_scores[decision_scores$gene == "TMEM158", ]
tm_lit <- literature_counts[literature_counts$gene == "TMEM158", ]
tm_gse <- gse45670_candidate[gse45670_candidate$gene == "TMEM158", ]
tm_scrna <- scrna_candidate[scrna_candidate$gene == "TMEM158", ]
tm_depmap <- depmap_candidate[depmap_candidate$gene == "TMEM158", ]
tm_prot <- proteomics_candidate[proteomics_candidate$gene == "TMEM158", ]

cross_layer <- data.frame(
  layer = c("TCGA axis-CAF discovery", "GSE45670 pretreatment validation",
            "GSE160269 epithelial branch", "GSE160269 CAF coupling",
            "DepMap ESCC basal branch", "ESCC proteogenomics coverage",
            "PubMed direct ESCC", "PubMed exact ESCC Ca2/UPR/CAF"),
  metric = c("rho", "rho", "rho", "rho", "rho", "covered_or_count", "count", "count"),
  value = c(
    ifelse(nrow(tm_decision) > 0, tm_decision$tcga_axis_caf_rho[1], NA_real_),
    ifelse(nrow(tm_gse) > 0, tm_gse$gse45670_axis_state_rho[1], NA_real_),
    ifelse(nrow(tm_scrna) > 0, tm_scrna$scrna_branch_rho[1], NA_real_),
    ifelse(nrow(tm_scrna) > 0, tm_scrna$scrna_caf_rho[1], NA_real_),
    ifelse(nrow(tm_depmap) > 0, tm_depmap$depmap_branch_rho[1], NA_real_),
    ifelse(nrow(tm_decision) > 0, tm_decision$proteomics_covered[1], NA_real_),
    ifelse(nrow(tm_lit) > 0, tm_lit$gene_escc_count[1], NA_real_),
    ifelse(nrow(tm_decision) > 0, tm_decision$exact_axis_duplication_count[1], NA_real_)
  ),
  interpretation = c(
    "positive discovery association",
    "external validation trend, FDR boundary in screen",
    "weak epithelial branch signal",
    "positive CAF coupling signal",
    "positive cell-line basal branch signal",
    "covered context, not direct causal protein validation",
    "novelty support if zero",
    "novelty support if zero"
  )
)
write_csv(cross_layer, file.path(branch_root, "04_results", "validation", "tmem158_cross_layer_evidence.csv"))

axis_ecology <- do.call(rbind, lapply(split(tumor_cor, tumor_cor$dataset), function(d) {
  getv <- function(metric, col) {
    z <- d[d$metric == metric, col]
    if (length(z) == 0) NA_real_ else z[1]
  }
  ca2 <- getv("Ca2_axis_score", "rho")
  perk <- getv("PERK_bias_index", "rho")
  caf <- getv("CAF_score", "rho")
  prot <- getv("Proteostasis_score", "rho")
  data.frame(
    dataset = unique(d$dataset),
    ca2_rho = ca2,
    ca2_fdr = getv("Ca2_axis_score", "FDR"),
    perk_bias_rho = perk,
    perk_bias_fdr = getv("PERK_bias_index", "FDR"),
    caf_rho = caf,
    caf_fdr = getv("CAF_score", "FDR"),
    proteostasis_rho = prot,
    proteostasis_fdr = getv("Proteostasis_score", "FDR"),
    interpretation = ifelse(is.finite(caf) && abs(caf) >= abs(ca2),
                            "ecology_dominant_or_CAF_coupled",
                            "axis_dominant_or_mixed")
  )
}))
write_csv(axis_ecology, file.path(branch_root, "04_results", "validation", "tmem158_axis_ecology_dissection.csv"))

negative_results <- data.frame(
  item = c("TMEM158 survival in TCGA", "GSE45670 validation FDR", "GSE160269 epithelial branch", "Proteogenomics protein direction", "PubMed exact mechanism overlap"),
  finding = c(
    ifelse(nrow(surv_rows) > 0 && all(is.na(surv_rows$p.value) | surv_rows$p.value >= 0.05),
           "No significant survival association in first-pass TCGA Cox", "Survival signal requires review"),
    ifelse(nrow(tm_gse) > 0 && tm_gse$gse45670_axis_state_fdr[1] >= 0.05,
           "External GSE45670 correlation is nominal or boundary after FDR", "External GSE45670 supported"),
    ifelse(nrow(tm_scrna) > 0 && tm_scrna$scrna_branch_fdr[1] >= 0.05,
           "Epithelial branch correlation does not pass FDR in screen", "Epithelial branch supported"),
    ifelse(nrow(tm_decision) > 0 && tm_decision$proteomics_positive[1] == 0,
           "Proteomics coverage is context only, not a positive directional protein result", "Proteomics positive"),
    ifelse(nrow(tm_decision) > 0 && tm_decision$exact_axis_duplication_count[1] == 0,
           "No exact overlap; this supports novelty but not biological proof", "Overlap detected")
  ),
  claim_effect = c("downgrade prognostic claim", "downgrade validation strength", "downgrade tumour-cell-intrinsic claim", "downgrade protein-validation claim", "keep novelty but avoid causal overclaim")
)
write_csv(negative_results, file.path(branch_root, "04_results", "qc", "negative_results.csv"))

readiness <- data.frame(
  gate = c("main biological axis", "lead candidate", "literature novelty", "external validation", "single-cell context", "cell-line feasibility", "protein/proteomics", "prognosis", "causal mechanism"),
  status = c("pass", "pass", "pass", "conditional", "conditional", "pass", "conditional", "weak", "not_proven"),
  evidence = c(
    "Ca2/UPR branch-state is the strongest existing public-data signal",
    "TMEM158 is lead_candidate in final decision branch",
    "PubMed direct ESCC and exact ESCC Ca2/UPR/CAF overlap are zero in VM audit",
    "GSE45670 rho positive but FDR boundary in candidate screen",
    "GSE160269 supports CAF coupling more than epithelial branch activation",
    "DepMap ESCC basal branch rho positive and expression feasible",
    "ESCC proteogenomics coverage is present but not positive directional proof",
    "First-pass TCGA survival is not expected to be strong; treat as secondary",
    "All evidence remains observational public-data"
  ),
  action_to_publish = c(
    "Make Ca2/UPR branch-state the paper core",
    "Use TMEM158 as computational lead, not as validated driver",
    "Complete full-text/table novelty gate before manuscript finalization",
    "Add one more independent external expression/axis validation if possible",
    "Frame as CAF-coupled stress ecology, not CD8 exhaustion causality",
    "Use for public-data model prioritization only",
    "Do not call this protein validation",
    "Avoid prognostic-biomarker headline",
    "Use association and hypothesis-generating language"
  )
)
write_csv(readiness, file.path(branch_root, "04_results", "qc", "publication_readiness_gate.csv"))

status <- data.frame(
  item = c("module_status", "lead_gene", "recommended_story", "tcga_samples_scored", "external_datasets_scored", "figures_created"),
  value = c("completed_first_pass", "TMEM158", "Ca2/UPR branch-state + TMEM158 lead candidate",
            nrow(tcga_surv), length(unique(sample_scores$batch)), "5")
)
write_csv(status, file.path(branch_root, "06_tables", "tmem158_primary_evidence_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  fig_data <- sample_scores[sample_scores$batch %in% c("TCGA", "GSE20347", "GSE45670", "GSE26886"), ]
  p1 <- ggplot(fig_data, aes(x = group, y = TMEM158, fill = group)) +
    geom_boxplot(outlier.shape = NA, width = 0.65) +
    geom_jitter(width = 0.15, size = 0.8, alpha = 0.55) +
    facet_wrap(~batch, scales = "free_y") +
    theme_bw(base_size = 10) +
    labs(title = "TMEM158 expression across public ESCC cohorts", x = NULL, y = "Batch-adjusted expression")
  plot_save(p1, file.path(branch_root, "05_figures", "figure1_tmem158_expression_public_cohorts"), 8, 5)

  p2 <- ggplot(tumor_cor, aes(x = metric, y = dataset, fill = rho)) +
    geom_tile(color = "white", linewidth = 0.3) +
    scale_fill_gradient2(low = "#2b6cb0", mid = "white", high = "#b83232", midpoint = 0, na.value = "grey85") +
    theme_bw(base_size = 9) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(title = "Tumour-internal TMEM158 axis coupling", x = NULL, y = NULL, fill = "Spearman rho")
  plot_save(p2, file.path(branch_root, "05_figures", "figure2_tmem158_axis_correlation_heatmap"), 9, 4.8)

  tcga_long <- rbind(
    data.frame(sample = tcga_surv$sample, TMEM158 = tcga_surv$TMEM158, metric = "Ca2 axis", value = tcga_surv$Ca2_axis_score),
    data.frame(sample = tcga_surv$sample, TMEM158 = tcga_surv$TMEM158, metric = "PERK bias", value = tcga_surv$PERK_bias_index),
    data.frame(sample = tcga_surv$sample, TMEM158 = tcga_surv$TMEM158, metric = "CAF score", value = tcga_surv$CAF_score)
  )
  p3 <- ggplot(tcga_long, aes(x = TMEM158, y = value)) +
    geom_point(size = 1.2, alpha = 0.65, color = "#2f5d62") +
    geom_smooth(method = "lm", se = TRUE, color = "#a6423a", linewidth = 0.7) +
    facet_wrap(~metric, scales = "free_y") +
    theme_bw(base_size = 10) +
    labs(title = "TCGA tumour-level TMEM158 stress-state associations", x = "TMEM158 expression", y = "Score")
  plot_save(p3, file.path(branch_root, "05_figures", "figure3_tcga_tmem158_stress_state_scatter"), 8, 4.8)

  if (exists("scrna") && nrow(scrna) > 0 && "CAF_score" %in% names(scrna)) {
    p4 <- ggplot(scrna, aes(x = TMEM158, y = CAF_score)) +
      geom_point(aes(size = n_cells), alpha = 0.65, color = "#4b6584") +
      geom_smooth(method = "lm", se = TRUE, color = "#b33939", linewidth = 0.7) +
      theme_bw(base_size = 10) +
      labs(title = "Single-cell pseudo-bulk TMEM158 and CAF-coupled ecology", x = "Epithelial TMEM158", y = "CAF score", size = "Epithelial cells")
    plot_save(p4, file.path(branch_root, "05_figures", "figure4_gse160269_tmem158_caf_coupling"), 6.5, 4.8)
  }

  cl <- cross_layer
  cl$display_value <- as.numeric(cl$value)
  p5 <- ggplot(cl, aes(x = reorder(layer, display_value), y = display_value, fill = interpretation)) +
    geom_col(width = 0.7) +
    coord_flip() +
    theme_bw(base_size = 9) +
    theme(legend.position = "bottom") +
    labs(title = "TMEM158 first-pass cross-layer evidence", x = NULL, y = "Evidence value")
  plot_save(p5, file.path(branch_root, "05_figures", "figure5_tmem158_cross_layer_evidence"), 8, 5.2)
}

report <- c(
  "# TMEM158-Ca2/UPR ESCC First-Pass Public-Data Report",
  "",
  paste0("Date: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
  "",
  "## Working Claim",
  "",
  "The current pure-bioinformatics manuscript direction is a Ca2/UPR branch-state-centered ESCC discovery study with TMEM158 as a prioritized upstream candidate. TMEM158 is not treated as a validated causal driver.",
  "",
  "## Main Positive Signals",
  "",
  paste0("- Final decision branch grade: ", ifelse(nrow(tm_decision) > 0, tm_decision$candidate_grade[1], "NA"),
         "; decision score=", ifelse(nrow(tm_decision) > 0, round(tm_decision$decision_score[1], 3), NA), "."),
  paste0("- TCGA axis-CAF rho=", ifelse(nrow(tm_decision) > 0, round(tm_decision$tcga_axis_caf_rho[1], 3), NA),
         "; GSE45670 rho=", ifelse(nrow(tm_gse) > 0, round(tm_gse$gse45670_axis_state_rho[1], 3), NA),
         "; DepMap branch rho=", ifelse(nrow(tm_depmap) > 0, round(tm_depmap$depmap_branch_rho[1], 3), NA), "."),
  paste0("- PubMed direct ESCC count=", ifelse(nrow(tm_lit) > 0, tm_lit$gene_escc_count[1], NA),
         "; exact ESCC Ca2/UPR/CAF overlap=", ifelse(nrow(tm_decision) > 0, tm_decision$exact_axis_duplication_count[1], NA), "."),
  "",
  "## Key Boundaries",
  "",
  "- This branch does not provide wet-lab validation.",
  "- Survival is secondary and should not be used as the title-level claim unless later analyses strengthen it.",
  "- Single-cell evidence currently supports CAF-coupled stress ecology more than a simple tumour-cell-autonomous activation model.",
  "- Recomputed dataset-level correlations suggest TMEM158 is better framed as an axis-ecology coupling candidate than as a simple Ca2-activation marker.",
  "- Proteogenomics coverage is context evidence, not direct TMEM158 protein mechanism validation.",
  "",
  "## Files",
  "",
  "- `04_results/qc/publication_readiness_gate.csv`",
  "- `04_results/validation/tmem158_cross_layer_evidence.csv`",
  "- `04_results/validation/tmem158_axis_ecology_dissection.csv`",
  "- `04_results/expression/tmem158_tumor_normal_tests.csv`",
  "- `04_results/enrichment/tmem158_axis_correlations_by_dataset.csv`",
  "- `04_results/immune/tmem158_scrna_ecosystem_correlations.csv`",
  "- `05_figures/figure1_tmem158_expression_public_cohorts.*`",
  "- `05_figures/figure2_tmem158_axis_correlation_heatmap.*`",
  "- `05_figures/figure3_tcga_tmem158_stress_state_scatter.*`",
  "- `05_figures/figure4_gse160269_tmem158_caf_coupling.*`",
  "- `05_figures/figure5_tmem158_cross_layer_evidence.*`"
)
writeLines(report, file.path(branch_root, "07_manuscript", "tmem158_caupr_first_pass_report.md"))

writeLines(c(
  "# Reviewer Risk Checklist",
  "",
  "- Do not claim TMEM158 is a validated driver.",
  "- Do not headline prognosis if TCGA survival remains weak.",
  "- Do not call proteogenomics coverage protein validation.",
  "- Do not describe TAC_high as a purely tumour-cell-intrinsic programme; GSE160269 signature localization is fibroblast/CAF-dominant.",
  "- Do not upgrade fibroblast/CAF localization into cell-cell causality or TMEM158-driven transcription.",
  "- Do not upgrade CAF-to-epithelial ligand-receptor bridge scores into CellChat-level signalling proof; write POSTN/collagen/FN1-integrin and MIF-CXCR4 as candidate bridges only.",
  "- Do not claim broad cytokine/growth-factor activation; IL6-family and growth-factor axes are not TAC_high-higher support in the current bridge analysis.",
  "- Do not overstate GSE221561 as a definitive independent validation cohort; it supports fibroblast-dominant TAC meta-ECM localization but has partial raw-library recovery and only six matched tumour libraries for bridge context.",
  "- Complete full-text and supplementary-table duplication gate before final manuscript.",
  "- Prioritize figure consolidation, formal references and manual novelty checks over adding more weak external layers.",
  "- Keep all methods explicitly public-data only."
), file.path(branch_root, "08_submission_strategy", "reviewer_risk_checklist.md"))

write_csv(data.frame(
  source = c("TCGA/GEO combat expression", "TCGA expression", "GSE160269 pseudo-bulk", "Axis-first screen", "Final decision PubMed audit"),
  path = c(
    file.path(source_root, "data/processed/tcga_geo_combat_expression_common_genes.rds"),
    file.path(source_root, "data/processed/tcga_esca_expression_symbol_log2.rds"),
    file.path(screen_root, "06_tables/gse160269_candidate_epithelial_pseudobulk.csv"),
    file.path(screen_root, "06_tables/gene_screening_score.csv"),
    file.path(decision_root, "06_tables/candidate_literature_audit_counts.csv")
  ),
  reuse_role = c("expression and axis scores", "TCGA tumour survival and scores", "single-cell epithelial expression", "candidate context", "novelty and duplication gate")
), file.path(branch_root, "02_data", "data_inventory.csv"))

writeLines(c(
  "# Master Log",
  "",
  paste0("- ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), ": Created TMEM158-Ca2/UPR ESCC first-pass public-data evidence branch.")
), file.path(branch_root, "00_project_log", "master_log.md"))

writeLines(c(
  "# Stage Summary",
  "",
  "First-pass TMEM158 branch completed. The branch supports a Ca2/UPR axis-centered manuscript direction with TMEM158 as lead computational candidate, while preserving survival, proteomics and causality boundaries."
), file.path(branch_root, "00_project_log", "stage_summary.md"))

writeLines(c(
  "# Decision Record",
  "",
  "Decision: continue pure bioinformatics manuscript construction by pivoting from SMIM14-core to TMEM158 lead-candidate plus Ca2/UPR branch-state.",
  "",
  "Reason: prior final decision branch selected TMEM158 as lead candidate, and the user explicitly wants continued pure-bioinformatics progress toward an original SCI paper."
), file.path(branch_root, "00_project_log", "decision_record.md"))

writeLines(c(
  "# Negative Results Log",
  "",
  "See `04_results/qc/negative_results.csv`."
), file.path(branch_root, "00_project_log", "negative_results_log.md"))

writeLines(c(
  "# Context Checkpoint",
  "",
  "Current branch objective: build a submission-oriented pure-public-data story around Ca2/UPR branch-state and TMEM158.",
  "",
  "Do not mix this branch with the older SMIM14-core manuscript except as comparator/history."
), file.path(branch_root, "00_project_log", "context_checkpoint.md"))

write_csv(data.frame(
  result = c("expression_tests", "axis_correlations", "survival", "scrna_ecosystem", "cross_layer_evidence", "readiness_gate"),
  path = c(
    "04_results/expression/tmem158_tumor_normal_tests.csv",
    "04_results/enrichment/tmem158_axis_correlations_by_dataset.csv",
    "04_results/survival/tmem158_tcga_survival.csv",
    "04_results/immune/tmem158_scrna_ecosystem_correlations.csv",
    "04_results/validation/tmem158_cross_layer_evidence.csv",
    "04_results/qc/publication_readiness_gate.csv"
  )
), file.path(branch_root, "04_results", "result_index.csv"))

write_log("TMEM158 first-pass public-data branch completed")
