#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
})

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
processed_dir <- file.path(branch_root, "02_data", "processed")
out_dir <- file.path(branch_root, "04_results", "gse221561")
fig_dir <- file.path(branch_root, "05_figures")
man_dir <- file.path(branch_root, "07_manuscript")
log_file <- file.path(branch_root, "logs", "tmem158_gse221561_tac_context_validation.log")
for (d in c(processed_dir, out_dir, fig_dir, man_dir, dirname(log_file))) {
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

zscore <- function(x) {
  x <- suppressWarnings(as.numeric(x))
  s <- sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  out <- as.numeric(scale(x))
  out[!is.finite(out)] <- 0
  out
}

mean_score <- function(df, genes, min_present = 2) {
  present <- intersect(genes, names(df))
  present <- present[vapply(df[present], function(x) sum(is.finite(as.numeric(x))) >= 3 &&
                              sd(as.numeric(x), na.rm = TRUE) > 0, logical(1))]
  if (length(present) < min_present) return(rep(NA_real_, nrow(df)))
  zscore(rowMeans(as.matrix(df[, present, drop = FALSE]), na.rm = TRUE))
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
  helper <- file.path(branch_root, "03_scripts", "Python", "extract_tmem158_gse221561_tac_targets.py")
  if (!file.exists(helper)) stop("Missing helper: ", helper)
  py <- choose_python()
  write_log(sprintf("Running GSE221561 TAC target extractor with %s", py))
  status <- system2(py, normalizePath(helper, mustWork = TRUE), stdout = log_file, stderr = log_file)
  if (!identical(status, 0L) && !identical(status, 0)) {
    stop("GSE221561 TAC target extractor failed with status ", status)
  }
}

make_wide <- function(long) {
  sub <- long[, c("group_id", "gene", "mean_log1p"), drop = FALSE]
  sub$mean_log1p <- suppressWarnings(as.numeric(sub$mean_log1p))
  wide <- reshape(sub, idvar = "group_id", timevar = "gene", direction = "wide")
  names(wide) <- sub("^mean_log1p\\.", "", names(wide))
  meta_cols <- c("group_id", "group_level", "library_name", "group_name", "Cell_type",
                 "Cell_type_sub", "Tissue_type", "Neoadjuvant", "n_cells")
  meta <- unique(long[, intersect(meta_cols, names(long)), drop = FALSE])
  merge(meta, wide, by = "group_id", all.x = TRUE)
}

add_scores <- function(df) {
  ca2_core <- c("STIM1", "ORAI1", "ATP2A2", "ITPR1", "ITPR2", "ITPR3")
  perk <- c("EIF2AK3", "ATF4", "DDIT3")
  ire1_atf6 <- c("ERN1", "XBP1", "ATF6")
  proteostasis <- c("HSPA5", "HSP90B1", "CANX", "CALR", "PDIA3", "PDIA4", "DNAJB9",
                    "HERPUD1", "PPP1R15A", "SEL1L", "EDEM1", "SYVN1", "DERL3")
  transport <- c("ABCC1", "ABCC2", "ABCC3", "ABCG2", "ABCB1", "SLC7A11", "GCLC",
                 "GCLM", "GSR", "GPX1", "GPX8", "NQO1", "HMOX1", "TXN", "TXNRD1",
                 "SOD2", "GSTP1")
  tac_meta <- c("POSTN", "COL6A3", "COL1A2", "CHST7", "COL3A1", "FAP", "SULF1",
                "COL1A1", "COL6A2", "SPRY2", "MMP2", "MMP11", "ACTA2", "FN1",
                "VIM", "TAGLN", "LUM", "DCN", "COL5A1", "COL5A2")
  caf_ecm <- c("COL1A1", "COL1A2", "COL3A1", "COL6A2", "COL6A3", "POSTN",
               "FAP", "ACTA2", "FN1", "TAGLN", "LUM", "DCN", "MMP2", "MMP11",
               "CXCL12", "TGFB1", "IL6")
  ecm_ligand <- c("POSTN", "COL1A1", "COL1A2", "COL3A1", "FN1")
  mif_ligand <- c("MIF", "SPP1", "INHBA")
  integrin_receptor <- c("ITGA1", "ITGA5", "ITGAV", "ITGB1", "ITGB3", "CD44")
  mif_receptor <- c("CXCR4", "CD74", "CD44", "ACVR2A")
  t_exhaust <- c("PDCD1", "LAG3", "HAVCR2", "TOX", "TIGIT", "CTLA4")
  cytotoxic <- c("CD8A", "CD8B", "GZMB", "PRF1", "NKG7", "IFNG")
  myeloid <- c("CD163", "MRC1", "SPP1", "APOE", "CCL18", "IL10", "TGFB1")

  df$TMEM158_z <- if ("TMEM158" %in% names(df)) zscore(df$TMEM158) else NA_real_
  df$Ca2_core_score <- mean_score(df, ca2_core)
  df$PERK_score <- mean_score(df, perk)
  df$IRE1_ATF6_score <- mean_score(df, ire1_atf6)
  df$Ca_PERK_core_score <- zscore(rowMeans(df[, c("TMEM158_z", "Ca2_core_score", "PERK_score"), drop = FALSE], na.rm = TRUE))
  df$Proteostasis_score <- mean_score(df, proteostasis)
  df$Transport_detox_score <- mean_score(df, transport)
  df$TAC_meta_ECM_score <- mean_score(df, tac_meta)
  df$CAF_ECM_score <- mean_score(df, caf_ecm)
  df$ECM_integrin_ligand_score <- mean_score(df, ecm_ligand)
  df$MIF_SPP1_ligand_score <- mean_score(df, mif_ligand)
  df$Integrin_receptor_score <- mean_score(df, integrin_receptor)
  df$MIF_axis_receptor_score <- mean_score(df, mif_receptor)
  df$Tcell_exhaustion_score <- mean_score(df, t_exhaust)
  df$Cytotoxic_score <- mean_score(df, cytotoxic)
  df$Myeloid_suppressive_score <- mean_score(df, myeloid)
  df
}

paired_celltype_test <- function(df, score, case = "Fibroblast", ref = "Epithelial") {
  sub <- df[df$group_level == "Cell_type" & df$Tissue_type == "Tumor" &
              df$Cell_type %in% c(case, ref), , drop = FALSE]
  keep <- sub[, c("library_name", "Cell_type", score), drop = FALSE]
  names(keep)[3] <- "score"
  wide <- reshape(keep, idvar = "library_name", timevar = "Cell_type", direction = "wide")
  case_col <- paste0("score.", case)
  ref_col <- paste0("score.", ref)
  if (!all(c(case_col, ref_col) %in% names(wide))) {
    return(data.frame(score = score, case = case, reference = ref, n_pairs = 0,
                      case_median = NA, reference_median = NA, delta = NA,
                      p.value = NA, stringsAsFactors = FALSE))
  }
  ok <- is.finite(wide[[case_col]]) & is.finite(wide[[ref_col]])
  p <- if (sum(ok) >= 3) suppressWarnings(wilcox.test(wide[[case_col]][ok], wide[[ref_col]][ok], paired = TRUE)$p.value) else NA_real_
  data.frame(
    score = score,
    case = case,
    reference = ref,
    n_pairs = sum(ok),
    case_median = median(wide[[case_col]][ok], na.rm = TRUE),
    reference_median = median(wide[[ref_col]][ok], na.rm = TRUE),
    delta = median(wide[[case_col]][ok] - wide[[ref_col]][ok], na.rm = TRUE),
    p.value = p,
    stringsAsFactors = FALSE
  )
}

safe_cor <- function(x, y) {
  ok <- is.finite(x) & is.finite(y)
  if (sum(ok) < 5 || length(unique(x[ok])) < 3 || length(unique(y[ok])) < 3) {
    return(c(n = sum(ok), rho = NA_real_, p.value = NA_real_))
  }
  ct <- suppressWarnings(cor.test(x[ok], y[ok], method = "spearman", exact = FALSE))
  c(n = sum(ok), rho = unname(ct$estimate), p.value = ct$p.value)
}

plot_save <- function(p, stem, width = 9.5, height = 6.2) {
  ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 320, bg = "white")
  ggsave(paste0(stem, ".pdf"), p, width = width, height = height, bg = "white")
  ggsave(paste0(stem, ".svg"), p, width = width, height = height, bg = "white")
}

write_log("Starting GSE221561 TAC context validation")
run_extractor()

long <- read_csv(file.path(processed_dir, "tmem158_gse221561_tac_target_pseudobulk_expression.csv"))
extract_status <- read_csv(file.path(out_dir, "tmem158_gse221561_tac_extract_status.csv"))
coverage <- read_csv(file.path(out_dir, "tmem158_gse221561_tac_target_gene_coverage.csv"))
wide <- add_scores(make_wide(long))
write_csv(wide, file.path(out_dir, "tmem158_gse221561_tac_group_scores.csv"))

celltype_tumor <- wide[wide$group_level == "Cell_type" & wide$Tissue_type == "Tumor", , drop = FALSE]
scores_to_test <- c("TMEM158_z", "Ca_PERK_core_score", "TAC_meta_ECM_score", "CAF_ECM_score",
                    "ECM_integrin_ligand_score", "MIF_SPP1_ligand_score", "Proteostasis_score",
                    "Transport_detox_score")
refs <- c("Epithelial", "T cell", "Myeloid", "Endothelial")
paired_tests <- do.call(rbind, lapply(scores_to_test, function(score) {
  do.call(rbind, lapply(refs, function(ref) paired_celltype_test(wide, score, "Fibroblast", ref)))
}))
paired_tests$FDR <- ave(paired_tests$p.value, paired_tests$score, FUN = function(x) p.adjust(x, method = "BH"))
paired_tests$evidence_call <- ifelse(is.finite(paired_tests$FDR) & paired_tests$delta > 0 & paired_tests$FDR < 0.10,
                                     "fibroblast_higher_FDR",
                                     ifelse(is.finite(paired_tests$p.value) & paired_tests$delta > 0 & paired_tests$p.value < 0.05,
                                            "fibroblast_higher_nominal", "not_fibroblast_higher_FDR"))
write_csv(paired_tests, file.path(out_dir, "tmem158_gse221561_tac_compartment_paired_tests.csv"))

sample_scores <- celltype_tumor[celltype_tumor$Cell_type %in% c("Epithelial", "Fibroblast", "T cell", "Myeloid"), , drop = FALSE]
sample_keep <- sample_scores[, c("library_name", "Neoadjuvant", "Cell_type", "TMEM158_z",
                                 "Ca_PERK_core_score", "TAC_meta_ECM_score", "CAF_ECM_score",
                                 "ECM_integrin_ligand_score", "MIF_SPP1_ligand_score",
                                 "Integrin_receptor_score", "MIF_axis_receptor_score",
                                 "Proteostasis_score", "Transport_detox_score",
                                 "Tcell_exhaustion_score", "Cytotoxic_score", "Myeloid_suppressive_score"), drop = FALSE]
sample_long <- sample_keep
wide_sample <- reshape(sample_keep, idvar = c("library_name", "Neoadjuvant"),
                       timevar = "Cell_type", direction = "wide")
names(wide_sample) <- gsub(" ", "_", names(wide_sample))
wide_sample$TAC_like_context_score <- zscore(rowMeans(wide_sample[, intersect(c(
  "TMEM158_z.Epithelial", "Ca_PERK_core_score.Epithelial", "CAF_ECM_score.Fibroblast",
  "ECM_integrin_ligand_score.Fibroblast", "Integrin_receptor_score.Epithelial"
), names(wide_sample)), drop = FALSE], na.rm = TRUE))
wide_sample$ECM_integrin_bridge_score <- zscore(rowMeans(wide_sample[, intersect(c(
  "ECM_integrin_ligand_score.Fibroblast", "Integrin_receptor_score.Epithelial"
), names(wide_sample)), drop = FALSE], na.rm = TRUE))
wide_sample$MIF_CXCR4_bridge_score <- zscore(rowMeans(wide_sample[, intersect(c(
  "MIF_SPP1_ligand_score.Fibroblast", "MIF_axis_receptor_score.Epithelial"
), names(wide_sample)), drop = FALSE], na.rm = TRUE))
write_csv(wide_sample, file.path(out_dir, "tmem158_gse221561_tac_matched_sample_scores.csv"))

cor_features <- intersect(c("ECM_integrin_bridge_score", "MIF_CXCR4_bridge_score",
                            "Proteostasis_score.Epithelial", "Transport_detox_score.Epithelial",
                            "Tcell_exhaustion_score.T_cell", "Myeloid_suppressive_score.Myeloid"),
                          names(wide_sample))
sample_cor <- do.call(rbind, lapply(cor_features, function(feature) {
  ct <- safe_cor(wide_sample$TAC_like_context_score, wide_sample[[feature]])
  data.frame(x_feature = "TAC_like_context_score", y_feature = feature,
             n = ct[["n"]], rho = ct[["rho"]], p.value = ct[["p.value"]],
             stringsAsFactors = FALSE)
}))
sample_cor$FDR <- p.adjust(sample_cor$p.value, method = "BH")
sample_cor$evidence_call <- ifelse(is.finite(sample_cor$FDR) & sample_cor$rho > 0 & sample_cor$FDR < 0.10,
                                   "positive_FDR",
                                   ifelse(is.finite(sample_cor$p.value) & sample_cor$rho > 0 & sample_cor$p.value < 0.05,
                                          "positive_nominal", "descriptive_or_boundary"))
write_csv(sample_cor, file.path(out_dir, "tmem158_gse221561_tac_matched_sample_correlations.csv"))

subtype_scores <- wide[wide$group_level == "Cell_type_sub" & wide$Tissue_type == "Tumor" &
                         is.finite(wide$TAC_meta_ECM_score) & wide$n_cells >= 5, , drop = FALSE]
subtype_summary <- aggregate(cbind(TAC_meta_ECM_score, CAF_ECM_score, ECM_integrin_ligand_score,
                                   Integrin_receptor_score, Proteostasis_score) ~ Cell_type + group_name,
                             data = subtype_scores, FUN = median, na.rm = TRUE)
subtype_counts <- aggregate(n_cells ~ Cell_type + group_name, data = subtype_scores, FUN = sum, na.rm = TRUE)
subtype_summary <- merge(subtype_summary, subtype_counts, by = c("Cell_type", "group_name"), all.x = TRUE)
subtype_summary <- subtype_summary[order(-subtype_summary$TAC_meta_ECM_score), ]
write_csv(subtype_summary, file.path(out_dir, "tmem158_gse221561_tac_subtype_signature_summary.csv"))

status_value <- function(item) {
  val <- extract_status$value[extract_status$item == item]
  if (length(val)) val[[1]] else NA
}
top_cell <- aggregate(TAC_meta_ECM_score ~ Cell_type, data = celltype_tumor, FUN = median, na.rm = TRUE)
top_cell <- top_cell[order(-top_cell$TAC_meta_ECM_score), , drop = FALSE]
top_pair <- paired_tests[paired_tests$score == "TAC_meta_ECM_score" & paired_tests$reference == "Epithelial", , drop = FALSE]
bridge_cor <- sample_cor[sample_cor$y_feature == "ECM_integrin_bridge_score", , drop = FALSE]
covered_genes <- unique(coverage$canonical_gene[toupper(as.character(coverage$covered)) == "TRUE"])
requested_genes <- unique(coverage$canonical_gene)
status <- data.frame(
  item = c("module_status", "source_extract_status", "libraries_parsed", "libraries_failed",
           "tumor_libraries_with_epithelial_fibroblast", "target_genes_requested",
           "target_genes_covered", "top_celltype_TAC_meta_ECM", "fibroblast_vs_epithelial_TAC_meta_delta",
           "fibroblast_vs_epithelial_TAC_meta_p", "TAC_like_ECM_integrin_bridge_rho",
           "TAC_like_ECM_integrin_bridge_p", "interpretation"),
  value = c("completed",
            status_value("module_status"),
            status_value("libraries_parsed"),
            status_value("libraries_failed"),
            sum(is.finite(wide_sample$TAC_like_context_score)),
            length(requested_genes),
            length(covered_genes),
            ifelse(nrow(top_cell), top_cell$Cell_type[[1]], NA),
            ifelse(nrow(top_pair), fmt(top_pair$delta[[1]]), NA),
            ifelse(nrow(top_pair), fmt_p(top_pair$p.value[[1]]), NA),
            ifelse(nrow(bridge_cor), fmt(bridge_cor$rho[[1]]), NA),
            ifelse(nrow(bridge_cor), fmt_p(bridge_cor$p.value[[1]]), NA),
            "Independent GSE221561 therapy-context scRNA validation; partial raw-library recovery and small matched-sample n"
  )
)
write_csv(status, file.path(out_dir, "tmem158_gse221561_tac_context_status.csv"))

plot_cell <- celltype_tumor[celltype_tumor$Cell_type %in% c("Epithelial", "Fibroblast", "T cell", "Myeloid", "Endothelial"), ]
plot_cell$Cell_type <- factor(plot_cell$Cell_type, levels = c("Epithelial", "Fibroblast", "T cell", "Myeloid", "Endothelial"))
p1 <- ggplot(plot_cell, aes(Cell_type, TAC_meta_ECM_score, color = Cell_type)) +
  geom_boxplot(width = 0.55, outlier.shape = NA, linewidth = 0.3, alpha = 0.12) +
  geom_point(aes(group = library_name), size = 2.2, alpha = 0.86,
             position = position_jitter(width = 0.08, height = 0)) +
  geom_line(aes(group = library_name), color = "grey72", linewidth = 0.35, alpha = 0.65) +
  scale_color_manual(values = c(Epithelial = "#2F6FBB", Fibroblast = "#B24745", `T cell` = "#4B8C57",
                                Myeloid = "#8A6FB0", Endothelial = "#C7852A")) +
  labs(title = "GSE221561 TAC_high ECM programme localization",
       subtitle = "Matched cell-type pseudo-bulk; partial library recovery is retained",
       x = NULL, y = "TAC meta-ECM score") +
  theme_bw(base_size = 11) +
  theme(legend.position = "none", plot.title = element_text(face = "bold"))
plot_save(p1, file.path(fig_dir, "figure19_gse221561_tac_context_validation"))

plot_sub <- head(subtype_summary, 18)
plot_sub$label <- factor(paste(plot_sub$Cell_type, plot_sub$group_name, sep = ": "),
                         levels = rev(paste(plot_sub$Cell_type, plot_sub$group_name, sep = ": ")))
p2 <- ggplot(plot_sub, aes(TAC_meta_ECM_score, label, fill = Cell_type)) +
  geom_col(width = 0.72) +
  scale_fill_manual(values = c(Epithelial = "#2F6FBB", Fibroblast = "#B24745", `T cell` = "#4B8C57",
                               Myeloid = "#8A6FB0", Endothelial = "#C7852A", `B cell` = "#6B6B6B",
                               `Mast cell` = "#C7852A")) +
  labs(title = "Top GSE221561 subpopulation TAC meta-ECM scores",
       subtitle = "Cell-type-sub summaries are exploratory and not independent samples",
       x = "Median TAC meta-ECM score", y = NULL, fill = "Compartment") +
  theme_bw(base_size = 10.5) +
  theme(plot.title = element_text(face = "bold"), legend.position = "right")
plot_save(p2, file.path(fig_dir, "figure20_gse221561_tac_subtype_signature_context"), width = 10.2, height = 6.8)

update_text <- c(
  "# GSE221561 independent TAC context validation update",
  "",
  sprintf("The GSE221561 therapy-context single-cell layer parsed %s of %s listed libraries from the existing RAW archive; %s libraries remained corrupted at gzip-member level and are retained as an explicit boundary.",
          status_value("libraries_parsed"), status_value("libraries_in_filelist"), status_value("libraries_failed")),
  "",
  sprintf("All requested TMEM158/TAC_high/ECM-integrin target genes were represented at feature level in the parsed libraries (%s/%s requested canonical genes covered).",
          length(covered_genes), length(requested_genes)),
  "",
  sprintf("In matched cell-type pseudo-bulk tumour samples, the top median TAC meta-ECM compartment was %s. Fibroblast-versus-epithelial TAC meta-ECM delta was %s (paired Wilcoxon P=%s).",
          ifelse(nrow(top_cell), top_cell$Cell_type[[1]], "NA"),
          ifelse(nrow(top_pair), fmt(top_pair$delta[[1]]), "NA"),
          ifelse(nrow(top_pair), fmt_p(top_pair$p.value[[1]]), "NA")),
  "",
  sprintf("A matched TAC-like context score showed a descriptive association with the ECM-integrin bridge score (rho=%s, P=%s; n=%s).",
          ifelse(nrow(bridge_cor), fmt(bridge_cor$rho[[1]]), "NA"),
          ifelse(nrow(bridge_cor), fmt_p(bridge_cor$p.value[[1]]), "NA"),
          ifelse(nrow(bridge_cor), bridge_cor$n[[1]], "NA")),
  "",
  "Interpretation: this layer provides independent treatment-context single-cell support for a TAC/ECM stromal context if the direction is concordant, but it is underpowered and partially parsed. It must be written as external context validation, not as proof of therapy resistance, ligand-receptor signalling, or TMEM158 causality."
)
writeLines(update_text, file.path(man_dir, "tmem158_gse221561_tac_context_validation_update.md"))

idx_path <- file.path(branch_root, "04_results", "result_index.csv")
idx <- read_csv(idx_path, required = FALSE)
new_idx <- data.frame(
  result = c("gse221561_tac_context_status", "gse221561_tac_group_scores",
             "gse221561_tac_compartment_tests", "gse221561_tac_matched_sample_scores",
             "gse221561_tac_matched_sample_correlations", "gse221561_tac_subtype_summary",
             "figure19_gse221561_tac_context_validation",
             "figure20_gse221561_tac_subtype_signature_context",
             "gse221561_tac_context_update"),
  path = c("04_results/gse221561/tmem158_gse221561_tac_context_status.csv",
           "04_results/gse221561/tmem158_gse221561_tac_group_scores.csv",
           "04_results/gse221561/tmem158_gse221561_tac_compartment_paired_tests.csv",
           "04_results/gse221561/tmem158_gse221561_tac_matched_sample_scores.csv",
           "04_results/gse221561/tmem158_gse221561_tac_matched_sample_correlations.csv",
           "04_results/gse221561/tmem158_gse221561_tac_subtype_signature_summary.csv",
           "05_figures/figure19_gse221561_tac_context_validation.png",
           "05_figures/figure20_gse221561_tac_subtype_signature_context.png",
           "07_manuscript/tmem158_gse221561_tac_context_validation_update.md"),
  stringsAsFactors = FALSE
)
if (!is.null(idx) && nrow(idx)) {
  if (!"result" %in% names(idx) && "artifact" %in% names(idx)) names(idx)[names(idx) == "artifact"] <- "result"
  idx <- idx[, c("result", "path")]
  idx <- idx[!idx$result %in% new_idx$result, , drop = FALSE]
  idx <- rbind(idx, new_idx)
} else {
  idx <- new_idx
}
write_csv(idx, idx_path)

write_log("GSE221561 TAC context validation completed")
