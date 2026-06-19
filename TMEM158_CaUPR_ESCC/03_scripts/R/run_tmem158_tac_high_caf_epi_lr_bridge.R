#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
})

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
out_dir <- file.path(branch_root, "04_results", "ligand_receptor")
fig_dir <- file.path(branch_root, "05_figures")
man_dir <- file.path(branch_root, "07_manuscript")
log_file <- file.path(branch_root, "logs", "tmem158_tac_high_caf_epi_lr_bridge.log")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(man_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)

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

zscore <- function(x) {
  x <- as.numeric(x)
  s <- sd(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  out <- (x - mean(x, na.rm = TRUE)) / s
  out[!is.finite(out)] <- 0
  out
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
  helper <- file.path(branch_root, "03_scripts", "Python", "extract_tac_high_caf_epi_lr_gse160269.py")
  if (!file.exists(helper)) stop("Missing helper: ", helper)
  py <- choose_python()
  write_log(sprintf("Running CAF-epithelial LR extractor with %s", py))
  status <- system2(py, normalizePath(helper, mustWork = TRUE), stdout = log_file, stderr = log_file)
  if (!identical(status, 0L) && !identical(status, 0)) {
    stop("CAF-epithelial LR extractor failed with status ", status)
  }
}

add_pairs <- function(category, ligands, receptors) {
  expand.grid(ligand = ligands, receptor = receptors, stringsAsFactors = FALSE) |>
    transform(category = category,
              pair_id = paste(ligand, receptor, sep = "_"),
              pair_label = paste0(ligand, "->", receptor))
}

lr_pairs <- rbind(
  add_pairs("ECM_integrin", "POSTN", c("ITGAV", "ITGB3", "ITGA5", "ITGB1")),
  add_pairs("ECM_integrin", c("COL1A1", "COL1A2", "COL3A1", "COL6A1", "COL6A2", "COL6A3"), c("ITGA1", "ITGA2", "ITGB1")),
  add_pairs("ECM_integrin", "FN1", c("ITGA5", "ITGB1", "ITGAV", "ITGB3")),
  add_pairs("ECM_integrin", "SPP1", c("CD44", "ITGAV", "ITGB1")),
  add_pairs("ECM_integrin", c("THBS1", "THBS2"), c("CD47", "ITGB1")),
  add_pairs("ECM_integrin", "TNC", c("ITGA9", "ITGB1")),
  add_pairs("Laminin_integrin", c("LAMB1", "LAMC1", "LAMA4"), c("ITGA6", "ITGB4")),
  add_pairs("TGF_beta_activin", c("TGFB1", "TGFB2", "TGFB3"), c("TGFBR1", "TGFBR2", "TGFBR3")),
  add_pairs("TGF_beta_activin", "INHBA", c("ACVR1B", "ACVR2A")),
  add_pairs("IL6_family", "IL6", c("IL6R", "IL6ST")),
  add_pairs("IL6_family", "LIF", c("LIFR", "IL6ST")),
  add_pairs("IL6_family", "OSM", c("OSMR", "IL6ST")),
  add_pairs("Chemokine", "CXCL12", c("CXCR4", "ACKR3")),
  add_pairs("Chemokine", "CCL2", "CCR2"),
  add_pairs("MIF_SPP1_axis", "MIF", c("CD74", "CXCR4", "CD44")),
  add_pairs("Growth_factor", "VEGFA", c("KDR", "FLT1", "NRP1")),
  add_pairs("Growth_factor", "HGF", "MET"),
  add_pairs("Growth_factor", c("FGF2", "FGF7"), c("FGFR1", "FGFR2")),
  add_pairs("Growth_factor", c("PDGFA", "PDGFB"), c("PDGFRA", "PDGFRB")),
  add_pairs("Developmental", "GAS6", "AXL"),
  add_pairs("Developmental", "WNT5A", c("FZD2", "FZD5", "ROR2")),
  add_pairs("Developmental", "JAG1", c("NOTCH1", "NOTCH2"))
)
lr_pairs <- unique(lr_pairs[, c("category", "ligand", "receptor", "pair_id", "pair_label")])
write_csv(lr_pairs, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_pair_catalog.csv"))

spearman_row <- function(data, x, y, label) {
  ok <- is.finite(data[[x]]) & is.finite(data[[y]])
  if (sum(ok) >= 5 && length(unique(data[[x]][ok])) > 2 && length(unique(data[[y]][ok])) > 2) {
    ct <- suppressWarnings(cor.test(data[[x]][ok], data[[y]][ok], method = "spearman", exact = FALSE))
    rho <- unname(ct$estimate)
    p <- ct$p.value
  } else {
    rho <- NA_real_
    p <- NA_real_
  }
  data.frame(feature = label, n = sum(ok), rho = rho, p.value = p)
}

wilcox_tac <- function(data, value_col) {
  hi <- data[[value_col]][data$TAC_high_group == "High"]
  lo <- data[[value_col]][data$TAC_high_group == "Low"]
  p <- if (sum(is.finite(hi)) >= 3 && sum(is.finite(lo)) >= 3) {
    suppressWarnings(wilcox.test(hi, lo, exact = FALSE)$p.value)
  } else NA_real_
  data.frame(
    n_TAC_high = sum(is.finite(hi)),
    n_other = sum(is.finite(lo)),
    median_TAC_high = median(hi, na.rm = TRUE),
    median_other = median(lo, na.rm = TRUE),
    delta_TAC_high_minus_other = median(hi, na.rm = TRUE) - median(lo, na.rm = TRUE),
    p.value = p
  )
}

plot_save <- function(p, stem, width = 9.5, height = 6) {
  ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggsave(paste0(stem, ".svg"), p, width = width, height = height)
}

write_log("Starting TAC_high CAF-to-epithelial ligand-receptor bridge module")
run_extractor()

gene_means <- read_csv(file.path(out_dir, "tmem158_tac_high_caf_epi_lr_gene_means.csv"))
state <- read_csv(file.path(branch_root, "02_data", "processed", "tmem158_scrna_ecology_state_scores.csv"))
sig_scores <- read_csv(file.path(branch_root, "04_results", "scrna_signature", "tmem158_tac_high_scrna_signature_compartment_scores.csv"))

gene_means$key <- paste(gene_means$compartment, gene_means$gene, sep = "_")
wide <- reshape(
  gene_means[, c("sample", "condition", "key", "mean_log1p_cp10k")],
  idvar = c("sample", "condition"),
  timevar = "key",
  direction = "wide"
)
names(wide) <- sub("^mean_log1p_cp10k\\.", "", names(wide))

sig_fib <- sig_scores[sig_scores$signature == "TAC_high_positive_top50" &
                        sig_scores$compartment == "Fibroblast",
                      c("sample", "signature_score")]
names(sig_fib)[2] <- "fibroblast_TAC_high_top50_signature"

state_keep <- c("sample", "TMEM158", "Ca2_axis_score", "PERK_bias_index", "UPR_composite",
                "CAF_score", "core_axis_state_score", "perk_caf_ecology_score",
                "ecology_subtype", "TAC_high_group")
state_keep <- intersect(state_keep, names(state))
dat <- merge(state[, state_keep, drop = FALSE], wide, by = "sample", all.x = TRUE)
dat <- merge(dat, sig_fib, by = "sample", all.x = TRUE)
dat$TAC_high_group <- ifelse(dat$TAC_high_group == "High", "High", "Low")

pair_score_rows <- list()
pair_test_rows <- list()
pair_cor_rows <- list()

for (i in seq_len(nrow(lr_pairs))) {
  pair <- lr_pairs[i, ]
  ligand_col <- paste0("Fibroblast_", pair$ligand)
  receptor_col <- paste0("Epithelial_", pair$receptor)
  if (!ligand_col %in% names(dat) || !receptor_col %in% names(dat)) next
  ligand_expr <- as.numeric(dat[[ligand_col]])
  receptor_expr <- as.numeric(dat[[receptor_col]])
  z_ligand <- zscore(ligand_expr)
  z_receptor <- zscore(receptor_expr)
  lr_score <- (z_ligand + z_receptor) / 2
  cohigh_score <- pmin(z_ligand, z_receptor)

  pair_df <- data.frame(
    sample = dat$sample,
    ecology_subtype = dat$ecology_subtype,
    TAC_high_group = dat$TAC_high_group,
    category = pair$category,
    ligand = pair$ligand,
    receptor = pair$receptor,
    pair_id = pair$pair_id,
    pair_label = pair$pair_label,
    fibroblast_ligand_expr = ligand_expr,
    epithelial_receptor_expr = receptor_expr,
    lr_score = lr_score,
    cohigh_score = cohigh_score,
    stringsAsFactors = FALSE
  )
  pair_score_rows[[length(pair_score_rows) + 1L]] <- pair_df

  wt <- wilcox_tac(pair_df, "lr_score")
  pair_test_rows[[length(pair_test_rows) + 1L]] <- cbind(pair[, c("category", "ligand", "receptor", "pair_id", "pair_label")], wt)

  corr_features <- intersect(c("fibroblast_TAC_high_top50_signature", "CAF_score", "core_axis_state_score",
                               "perk_caf_ecology_score", "Ca2_axis_score", "PERK_bias_index",
                               "UPR_composite", "TMEM158"), names(dat))
  tmp <- cbind(pair_df[, c("sample", "lr_score")], dat[, corr_features, drop = FALSE])
  for (feature in corr_features) {
    cr <- spearman_row(tmp, "lr_score", feature, feature)
    pair_cor_rows[[length(pair_cor_rows) + 1L]] <- cbind(pair[, c("category", "ligand", "receptor", "pair_id", "pair_label")], cr)
  }
}

pair_scores <- do.call(rbind, pair_score_rows)
pair_tests <- do.call(rbind, pair_test_rows)
pair_cor <- do.call(rbind, pair_cor_rows)
pair_tests$FDR <- p.adjust(pair_tests$p.value, method = "BH")
pair_tests$boundary_call <- ifelse(pair_tests$FDR < 0.10 & pair_tests$delta_TAC_high_minus_other > 0,
                                   "TAC_high_higher_FDR",
                                   ifelse(pair_tests$p.value < 0.05 & pair_tests$delta_TAC_high_minus_other > 0,
                                          "TAC_high_higher_nominal", "not_FDR_TAC_high_higher"))
pair_cor$FDR <- ave(pair_cor$p.value, pair_cor$feature, FUN = function(x) p.adjust(x, method = "BH"))
pair_cor$boundary_call <- ifelse(pair_cor$FDR < 0.10 & pair_cor$rho > 0,
                                 "positive_FDR", "not_positive_FDR")

write_csv(pair_scores, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_pair_scores.csv"))
write_csv(pair_tests, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_pair_tests.csv"))
write_csv(pair_cor, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_pair_correlations.csv"))

axis_scores <- aggregate(lr_score ~ sample + ecology_subtype + TAC_high_group + category, data = pair_scores, FUN = mean)
axis_wide <- reshape(axis_scores, idvar = c("sample", "ecology_subtype", "TAC_high_group"),
                     timevar = "category", direction = "wide")
names(axis_wide) <- sub("^lr_score\\.", "", names(axis_wide))
axis_wide$CAF_to_epithelial_LR_composite <- rowMeans(axis_wide[, setdiff(names(axis_wide), c("sample", "ecology_subtype", "TAC_high_group")), drop = FALSE], na.rm = TRUE)
write_csv(axis_wide, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_axis_scores.csv"))

axis_tests <- do.call(rbind, lapply(setdiff(names(axis_wide), c("sample", "ecology_subtype", "TAC_high_group")), function(feature) {
  out <- wilcox_tac(axis_wide, feature)
  cbind(data.frame(axis = feature), out)
}))
axis_tests$FDR <- p.adjust(axis_tests$p.value, method = "BH")
axis_tests$boundary_call <- ifelse(axis_tests$FDR < 0.10 & axis_tests$delta_TAC_high_minus_other > 0,
                                   "TAC_high_higher_FDR",
                                   ifelse(axis_tests$p.value < 0.05 & axis_tests$delta_TAC_high_minus_other > 0,
                                          "TAC_high_higher_nominal", "not_FDR_TAC_high_higher"))
write_csv(axis_tests, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_axis_tests.csv"))

axis_cor_rows <- list()
axis_merged <- merge(axis_wide, dat[, intersect(c("sample", "fibroblast_TAC_high_top50_signature", "CAF_score",
                                                  "core_axis_state_score", "perk_caf_ecology_score",
                                                  "Ca2_axis_score", "PERK_bias_index", "UPR_composite",
                                                  "TMEM158"), names(dat)), drop = FALSE],
                     by = "sample", all.x = TRUE)
axis_features <- setdiff(names(axis_wide), c("sample", "ecology_subtype", "TAC_high_group"))
target_features <- setdiff(names(axis_merged), c(names(axis_wide)))
for (axis in axis_features) {
  for (feature in target_features) {
    cr <- spearman_row(axis_merged, axis, feature, feature)
    axis_cor_rows[[length(axis_cor_rows) + 1L]] <- cbind(data.frame(axis = axis), cr)
  }
}
axis_cor <- do.call(rbind, axis_cor_rows)
axis_cor$FDR <- ave(axis_cor$p.value, axis_cor$feature, FUN = function(x) p.adjust(x, method = "BH"))
write_csv(axis_cor, file.path(out_dir, "tmem158_tac_high_caf_epi_lr_axis_correlations.csv"))

top_pairs <- pair_tests[is.finite(pair_tests$delta_TAC_high_minus_other) &
                          pair_tests$delta_TAC_high_minus_other > 0, ]
top_pairs <- top_pairs[order(top_pairs$FDR, -top_pairs$delta_TAC_high_minus_other), ]
top_pairs <- head(top_pairs, 24)
top_pairs$pair_label <- factor(top_pairs$pair_label, levels = rev(top_pairs$pair_label))
top_pairs$neg_log10_FDR <- -log10(pmax(top_pairs$FDR, .Machine$double.xmin))

p1 <- ggplot(top_pairs, aes(x = delta_TAC_high_minus_other, y = pair_label)) +
  geom_vline(xintercept = 0, color = "grey75", linewidth = 0.35) +
  geom_point(aes(size = neg_log10_FDR, color = category), alpha = 0.9) +
  scale_size_continuous(range = c(2, 7)) +
  labs(
    title = "CAF-to-epithelial ligand-receptor candidates enriched in TAC_high",
    subtitle = "Scores combine fibroblast ligand and epithelial receptor pseudo-bulk expression in GSE160269",
    x = "Median LR score difference: TAC_high - other",
    y = NULL,
    size = "-log10 FDR",
    color = "Axis"
  ) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(), legend.position = "right")
plot_save(p1, file.path(fig_dir, "figure17_tac_high_caf_epi_lr_bridge"), width = 9.5, height = 6.4)

axis_plot <- axis_scores
axis_plot$group <- ifelse(axis_plot$TAC_high_group == "High", "TAC_high", "Other")
axis_plot$category <- factor(axis_plot$category, levels = names(sort(tapply(axis_plot$lr_score, axis_plot$category, median, na.rm = TRUE), decreasing = TRUE)))
p2 <- ggplot(axis_plot, aes(x = group, y = lr_score, fill = group)) +
  geom_boxplot(width = 0.62, outlier.shape = NA, alpha = 0.75) +
  geom_jitter(width = 0.12, size = 1.15, alpha = 0.55, color = "grey20") +
  facet_wrap(~ category, scales = "free_y", ncol = 3) +
  scale_fill_manual(values = c(TAC_high = "#c43c39", Other = "#8f99a8")) +
  labs(
    title = "Pathway-level CAF-to-epithelial ligand-receptor bridge",
    subtitle = "TAC_high labels are rule-defined at matched GSE160269 pseudo-bulk level",
    x = NULL,
    y = "Mean LR score"
  ) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(), legend.position = "none")
plot_save(p2, file.path(fig_dir, "figure18_tac_high_caf_epi_lr_axis_scores"), width = 10.2, height = 7)

positive_axes <- axis_tests[is.finite(axis_tests$delta_TAC_high_minus_other) &
                              axis_tests$delta_TAC_high_minus_other > 0, , drop = FALSE]
if (nrow(positive_axes) > 0) {
  top_axis <- positive_axes[order(positive_axes$FDR, -positive_axes$delta_TAC_high_minus_other), ][1, , drop = FALSE]
} else {
  top_axis <- axis_tests[order(axis_tests$FDR, -axis_tests$delta_TAC_high_minus_other), ][1, , drop = FALSE]
}
positive_pairs <- pair_tests[is.finite(pair_tests$delta_TAC_high_minus_other) &
                               pair_tests$delta_TAC_high_minus_other > 0, , drop = FALSE]
if (nrow(positive_pairs) > 0) {
  top_pair <- positive_pairs[order(positive_pairs$FDR, -positive_pairs$delta_TAC_high_minus_other), ][1, , drop = FALSE]
} else {
  top_pair <- pair_tests[order(pair_tests$FDR, -pair_tests$delta_TAC_high_minus_other), ][1, , drop = FALSE]
}
status <- data.frame(
  item = c("module_status", "lr_pairs_defined", "lr_pairs_scored", "tumor_samples_scored",
           "TAC_high_higher_FDR_pairs", "TAC_high_higher_FDR_axes",
           "top_pair", "top_pair_FDR", "top_axis", "top_axis_FDR",
           "interpretation"),
  value = c("completed", nrow(lr_pairs), length(unique(pair_scores$pair_id)), length(unique(pair_scores$sample)),
            sum(pair_tests$boundary_call == "TAC_high_higher_FDR", na.rm = TRUE),
            sum(axis_tests$boundary_call == "TAC_high_higher_FDR", na.rm = TRUE),
            top_pair$pair_label, fmt(top_pair$FDR, 4),
            top_axis$axis, fmt(top_axis$FDR, 4),
            "Candidate CAF-to-epithelial ligand-receptor bridge; association only"),
  stringsAsFactors = FALSE
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_tac_high_caf_epi_lr_bridge_status.csv"))

report <- c(
  "# TAC_high CAF-to-Epithelial Ligand-Receptor Bridge",
  "",
  "This module tested whether the fibroblast/CAF-localized TAC_high programme is accompanied by candidate CAF-to-epithelial ligand-receptor bridges in matched GSE160269 pseudo-bulk profiles.",
  "",
  "## Key Results",
  "",
  paste0("- Curated ligand-receptor pairs defined: ", nrow(lr_pairs), "."),
  paste0("- Ligand-receptor pairs scored in matched tumour samples: ", length(unique(pair_scores$pair_id)), "."),
  paste0("- Tumour samples scored: ", length(unique(pair_scores$sample)), "."),
  paste0("- TAC_high-higher FDR-positive LR pairs: ", sum(pair_tests$boundary_call == "TAC_high_higher_FDR", na.rm = TRUE), "."),
  paste0("- TAC_high-higher FDR-positive LR axes: ", sum(axis_tests$boundary_call == "TAC_high_higher_FDR", na.rm = TRUE), "."),
  paste0("- Top LR pair: `", top_pair$pair_label, "` (delta=", fmt(top_pair$delta_TAC_high_minus_other), ", FDR=", fmt_p(top_pair$FDR), ")."),
  paste0("- Top LR axis: `", top_axis$axis, "` (delta=", fmt(top_axis$delta_TAC_high_minus_other), ", FDR=", fmt_p(top_axis$FDR), ")."),
  "",
  "## Interpretation Boundary",
  "",
  "This is a matched pseudo-bulk candidate bridge analysis. It supports ligand-receptor hypotheses linking CAF/ECM localization to epithelial stress ecology, but it does not prove physical cell-cell communication, ligand causality, receptor activation, or TMEM158-driven signalling."
)
writeLines(report, file.path(man_dir, "tmem158_tac_high_caf_epi_lr_bridge_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
new_index <- data.frame(
  result = c("tac_high_caf_epi_lr_status", "tac_high_caf_epi_lr_pair_tests",
             "tac_high_caf_epi_lr_axis_tests", "figure17_tac_high_caf_epi_lr_bridge",
             "figure18_tac_high_caf_epi_lr_axis_scores", "tac_high_caf_epi_lr_update"),
  path = c("04_results/qc/tmem158_tac_high_caf_epi_lr_bridge_status.csv",
           "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_tests.csv",
           "04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_tests.csv",
           "05_figures/figure17_tac_high_caf_epi_lr_bridge.png",
           "05_figures/figure18_tac_high_caf_epi_lr_axis_scores.png",
           "07_manuscript/tmem158_tac_high_caf_epi_lr_bridge_update.md"),
  stringsAsFactors = FALSE
)
if (file.exists(index_path)) {
  old <- read.csv(index_path, check.names = FALSE)
  if (!"result" %in% names(old) && "artifact" %in% names(old)) names(old)[names(old) == "artifact"] <- "result"
  old <- old[!old$result %in% new_index$result, , drop = FALSE]
  write_csv(rbind(old, new_index), index_path)
} else {
  write_csv(new_index, index_path)
}

write_log("TAC_high CAF-to-epithelial ligand-receptor bridge module completed")
