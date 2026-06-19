#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
project_root <- normalizePath(getwd(), mustWork = TRUE)
source_root <- file.path(project_root, "SMIM14_CaUPR_ESCC")
log_file <- file.path(branch_root, "logs", "tmem158_tac_high_transcriptome_program.log")
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

plot_save <- function(p, stem, width = 8, height = 5) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height)
  TRUE
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

signed_stouffer_genes <- function(tab) {
  tab <- tab[is.finite(tab$P.Value) & is.finite(tab$logFC), ]
  if (nrow(tab) == 0) return(NULL)
  split_tab <- split(tab, tab$gene)
  out <- lapply(split_tab, function(d) {
    p <- pmax(d$P.Value, 1e-300)
    z <- stats::qnorm(p / 2, lower.tail = FALSE) * sign(d$logFC)
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

geneset_enrichment <- function(meta, gene_sets, model_name, min_size = 8, max_size = 500) {
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
      model = model_name,
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
  ifelse(nchar(x) > 56, paste0(substr(x, 1, 53), "..."), x)
}

write_log("Reading expression matrix, TAC_high states and gene sets")

if (!requireNamespace("limma", quietly = TRUE)) stop("limma package is required for transcriptome module")
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("ggplot2 package is required for transcriptome module")

expr <- readRDS(file.path(source_root, "data", "processed", "tcga_geo_combat_expression_common_genes.rds"))
state_scores <- read_csv(file.path(branch_root, "02_data", "processed", "tmem158_tumor_ecology_state_scores.csv"))

required <- c("sample", "dataset", "ecology_subtype", "core_high", "caf_high")
missing <- setdiff(required, names(state_scores))
if (length(missing) > 0) stop("Missing required state-score columns: ", paste(missing, collapse = ", "))

common_samples <- intersect(state_scores$sample, colnames(expr))
if (length(common_samples) < 50) stop("Too few matched expression/state samples")
state_scores <- state_scores[match(common_samples, state_scores$sample), , drop = FALSE]
expr <- expr[, common_samples, drop = FALSE]

state_scores$tac_high_num <- as.numeric(state_scores$ecology_subtype == "TAC_high")
state_scores$core_high_num <- as.numeric(as.logical(state_scores$core_high))
state_scores$caf_high_num <- as.numeric(as.logical(state_scores$caf_high))

custom_sets <- list(
  CUSTOM_DRUG_EFFLUX_TRANSPORT = c("ABCB1", "ABCB8", "ABCC1", "ABCC2", "ABCC3", "ABCC4", "ABCG2", "ATP7A", "ATP7B", "SLC31A1"),
  CUSTOM_ER_PROTEOSTASIS = c("HSPA5", "HSP90B1", "PDIA4", "DNAJB9", "HERPUD1", "CALR", "CANX", "EDEM1", "SEL1L", "VCP", "DERL1", "DERL2", "DERL3"),
  CUSTOM_UPR_PERK = c("EIF2AK3", "ATF4", "DDIT3", "PPP1R15A", "DNAJC3", "TRIB3", "ASNS", "SLC7A11"),
  CUSTOM_UPR_IRE1 = c("ERN1", "XBP1", "HSPA5", "DNAJB9", "HERPUD1", "EDEM1"),
  CUSTOM_UPR_ATF6 = c("ATF6", "HSPA5", "HSP90B1", "PDIA4", "CALR", "CANX", "SEL1L"),
  CUSTOM_CAF_ECM = c("ACTA2", "FAP", "COL1A1", "COL1A2", "COL3A1", "COL5A1", "COL6A1", "DCN", "PDPN", "TAGLN", "THY1", "CXCL12"),
  CUSTOM_TGF_BETA_CAF = c("TGFB1", "TGFBR1", "TGFBR2", "SMAD2", "SMAD3", "SMAD4", "SERPINE1", "CTGF", "COL1A1", "COL1A2"),
  CUSTOM_REDox_GLUTATHIONE = c("GCLC", "GCLM", "GSR", "GSTP1", "GPX1", "GPX2", "GPX3", "GPX4", "SOD1", "SOD2", "NQO1", "TXNRD1", "HMOX1"),
  CUSTOM_SURVIVAL_APOPTOSIS = c("BCL2", "BCL2L1", "MCL1", "BIRC5", "BIRC3", "XIAP", "CASP3", "CASP7", "BAX", "BAK1"),
  CUSTOM_TCELL_EXHAUSTION = c("PDCD1", "LAG3", "HAVCR2", "TOX", "CTLA4", "TIGIT", "ENTPD1", "CXCL13", "EOMES")
)

hallmark_sets <- read_gmt(file.path(source_root, "data", "external", "msigdb_hallmark_symbols.gmt"))
reactome_sets <- read_gmt(file.path(source_root, "data", "external", "msigdb_reactome_symbols.gmt"))
gene_sets <- c(custom_sets, hallmark_sets, reactome_sets)

write_log(sprintf("Matched %d genes x %d tumor samples", nrow(expr), ncol(expr)))

per_cohort <- data.frame()
model_status <- data.frame()
for (ds in sort(unique(state_scores$dataset))) {
  idx <- which(state_scores$dataset == ds)
  d <- state_scores[idx, , drop = FALSE]
  e <- expr[, idx, drop = FALSE]
  n_tac <- sum(d$tac_high_num == 1, na.rm = TRUE)
  n_other <- sum(d$tac_high_num == 0, na.rm = TRUE)
  if (n_tac >= 3 && n_other >= 3) {
    design <- stats::model.matrix(~ tac_high_num, data = d)
    fit <- limma::eBayes(limma::lmFit(e, design))
    tt <- limma::topTable(fit, coef = "tac_high_num", number = Inf, sort.by = "none")
    tt$gene <- rownames(tt)
    tt$dataset <- ds
    tt$model <- "TAC_high_vs_other"
    tt$n_samples <- nrow(d)
    tt$n_high <- n_tac
    tt$n_low <- n_other
    per_cohort <- rbind(per_cohort, tt[, c("model", "dataset", "gene", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "n_samples", "n_high", "n_low")])
    model_status <- rbind(model_status, data.frame(model = "TAC_high_vs_other", dataset = ds, status = "completed",
                                                   n_samples = nrow(d), n_high = n_tac, n_low = n_other))
  } else {
    model_status <- rbind(model_status, data.frame(model = "TAC_high_vs_other", dataset = ds, status = "skipped_small_groups",
                                                   n_samples = nrow(d), n_high = n_tac, n_low = n_other))
  }

  subtype_counts <- table(d$ecology_subtype)
  all_four_ok <- all(c("TAC_high", "Axis_only", "CAF_only", "TAC_low") %in% names(subtype_counts)) &&
    all(subtype_counts[c("TAC_high", "Axis_only", "CAF_only", "TAC_low")] >= 3)
  if (all_four_ok) {
    design <- stats::model.matrix(~ core_high_num * caf_high_num, data = d)
    fit <- limma::eBayes(limma::lmFit(e, design))
    coef_name <- "core_high_num:caf_high_num"
    tt <- limma::topTable(fit, coef = coef_name, number = Inf, sort.by = "none")
    tt$gene <- rownames(tt)
    tt$dataset <- ds
    tt$model <- "Core_CAF_interaction"
    tt$n_samples <- nrow(d)
    tt$n_high <- sum(d$ecology_subtype == "TAC_high")
    tt$n_low <- sum(d$ecology_subtype != "TAC_high")
    per_cohort <- rbind(per_cohort, tt[, c("model", "dataset", "gene", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "n_samples", "n_high", "n_low")])
    model_status <- rbind(model_status, data.frame(model = "Core_CAF_interaction", dataset = ds, status = "completed",
                                                   n_samples = nrow(d), n_high = sum(d$ecology_subtype == "TAC_high"),
                                                   n_low = sum(d$ecology_subtype != "TAC_high")))
  } else {
    model_status <- rbind(model_status, data.frame(model = "Core_CAF_interaction", dataset = ds, status = "skipped_unbalanced_four_state",
                                                   n_samples = nrow(d), n_high = sum(d$ecology_subtype == "TAC_high"),
                                                   n_low = sum(d$ecology_subtype != "TAC_high")))
  }
}

write_csv(per_cohort, file.path(branch_root, "04_results", "transcriptome", "tmem158_tac_high_per_cohort_limma.csv"))
write_csv(model_status, file.path(branch_root, "04_results", "qc", "tmem158_tac_high_transcriptome_model_status.csv"))

meta <- do.call(rbind, lapply(split(per_cohort, per_cohort$model), function(x) {
  ans <- signed_stouffer_genes(x)
  if (is.null(ans) || nrow(ans) == 0) return(NULL)
  ans$model <- unique(x$model)[1]
  ans[, c("model", setdiff(names(ans), "model"))]
}))
meta <- meta[order(meta$model, meta$meta_p), ]
write_csv(meta, file.path(branch_root, "04_results", "transcriptome", "tmem158_tac_high_meta_differential_genes.csv"))

enrichment <- do.call(rbind, lapply(split(meta, meta$model), function(m) {
  model_name <- unique(m$model)[1]
  geneset_enrichment(m, gene_sets, model_name)
}))
if (is.null(enrichment) || nrow(enrichment) == 0) enrichment <- data.frame()
write_csv(enrichment, file.path(branch_root, "04_results", "transcriptome", "tmem158_tac_high_geneset_enrichment.csv"))

top_genes <- do.call(rbind, lapply(split(meta, meta$model), function(m) {
  m <- m[order(m$meta_p), ]
  head(m, 200)
}))
write_csv(top_genes, file.path(branch_root, "04_results", "transcriptome", "tmem158_tac_high_top_meta_genes.csv"))

status <- data.frame(
  item = c(
    "module_status", "matched_genes", "matched_tumor_samples", "datasets",
    "tac_high_vs_other_completed_cohorts", "interaction_completed_cohorts",
    "tac_high_vs_other_positive_meta_FDR_0.10", "interaction_positive_meta_FDR_0.10",
    "top_tac_high_gene", "top_interaction_gene",
    "top_positive_custom_or_msigdb_pathway", "interpretation"
  ),
  value = c(
    "completed",
    nrow(expr),
    ncol(expr),
    paste(sort(unique(state_scores$dataset)), collapse = ";"),
    sum(model_status$model == "TAC_high_vs_other" & model_status$status == "completed"),
    sum(model_status$model == "Core_CAF_interaction" & model_status$status == "completed"),
    sum(meta$model == "TAC_high_vs_other" & meta$meta_FDR < 0.10 & meta$combined_z > 0, na.rm = TRUE),
    sum(meta$model == "Core_CAF_interaction" & meta$meta_FDR < 0.10 & meta$combined_z > 0, na.rm = TRUE),
    meta$gene[which(meta$model == "TAC_high_vs_other")[1]],
    meta$gene[which(meta$model == "Core_CAF_interaction")[1]],
    ifelse(nrow(enrichment) > 0, enrichment$gene_set[order(enrichment$p.value)][1], NA_character_),
    "Data-driven TAC_high transcriptome and core-by-CAF interaction models; association only"
  )
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_tac_high_transcriptome_program_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE) && nrow(enrichment) > 0) {
  library(ggplot2)
  epos <- enrichment[enrichment$direction == "positive" & is.finite(enrichment$p.value), ]
  epos$source <- ifelse(grepl("^HALLMARK_", epos$gene_set), "Hallmark",
                        ifelse(grepl("^REACTOME_", epos$gene_set), "Reactome", "Custom"))
  epos <- epos[order(epos$model, epos$FDR, -epos$delta_mean_z), ]
  plot_df <- do.call(rbind, lapply(split(epos, epos$model), function(x) head(x, 14)))
  plot_df$label <- clean_set_label(plot_df$gene_set)
  plot_df$label <- factor(plot_df$label, levels = rev(unique(plot_df$label[order(plot_df$delta_mean_z)])))
  p <- ggplot(plot_df, aes(x = delta_mean_z, y = label)) +
    geom_vline(xintercept = 0, colour = "grey70", linewidth = 0.35) +
    geom_point(aes(size = n_present, colour = pmin(FDR, 0.25)), alpha = 0.9) +
    scale_colour_gradient(low = "#b91c1c", high = "#2563eb", name = "FDR cap 0.25") +
    scale_size_continuous(range = c(2, 6), name = "Genes") +
    facet_wrap(~ model, scales = "free_y") +
    labs(
      title = "Data-driven TAC_high transcriptome programs",
      subtitle = "Gene-set enrichment from TAC_high differential and core-by-CAF interaction meta-statistics",
      x = "Mean combined-z difference for genes in set",
      y = NULL
    ) +
    theme_bw(base_size = 9) +
    theme(
      plot.title = element_text(face = "bold", size = 12),
      plot.subtitle = element_text(size = 9, colour = "grey35"),
      panel.grid.minor = element_blank(),
      strip.text = element_text(face = "bold"),
      axis.text.y = element_text(size = 7.5)
    )
  plot_save(p, file.path(branch_root, "05_figures", "figure13_tac_high_transcriptome_programs"), width = 10, height = 7)
}

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  interaction_meta <- meta[meta$model == "Core_CAF_interaction", ]
  if (nrow(interaction_meta) > 0) {
    ordered_genes <- head(interaction_meta$gene[order(interaction_meta$meta_p)], 35)
    h <- per_cohort[per_cohort$model == "Core_CAF_interaction" & per_cohort$gene %in% ordered_genes, ]
    h$gene <- factor(h$gene, levels = rev(ordered_genes))
    p2 <- ggplot(h, aes(x = dataset, y = gene, fill = logFC)) +
      geom_tile(colour = "white", linewidth = 0.15) +
      scale_fill_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = 0,
                           name = "Interaction\ncoefficient") +
      labs(
        title = "Core-by-CAF interaction genes defining TAC_high",
        subtitle = "Positive values indicate expression beyond additive core-high and CAF-high components",
        x = NULL,
        y = NULL
      ) +
      theme_bw(base_size = 9) +
      theme(
        plot.title = element_text(face = "bold", size = 12),
        plot.subtitle = element_text(size = 9, colour = "grey35"),
        panel.grid = element_blank(),
        axis.text.x = element_text(angle = 25, hjust = 1),
        axis.text.y = element_text(size = 7.5)
      )
    plot_save(p2, file.path(branch_root, "05_figures", "figure14_tac_high_interaction_gene_heatmap"), width = 7.5, height = 8.5)
  }
}

fmt <- function(x, digits = 3) {
  ifelse(is.na(x), "NA", formatC(as.numeric(x), format = "f", digits = digits))
}
fmt_p <- function(x) {
  ifelse(is.na(x), "NA", ifelse(as.numeric(x) < 0.001, "<0.001", sprintf("%.3f", as.numeric(x))))
}

top_model <- function(model_name) {
  m <- meta[meta$model == model_name, ]
  if (nrow(m) == 0) return(data.frame(gene = NA, combined_z = NA, meta_p = NA, meta_FDR = NA))
  m[order(m$meta_p), ][1, c("gene", "combined_z", "meta_p", "meta_FDR")]
}
top_enrich <- function(model_name) {
  e <- enrichment[enrichment$model == model_name & enrichment$direction == "positive", ]
  if (nrow(e) == 0) return(data.frame(gene_set = NA, delta_mean_z = NA, p.value = NA, FDR = NA))
  e[order(e$p.value), ][1, c("gene_set", "delta_mean_z", "p.value", "FDR")]
}

tac_top <- top_model("TAC_high_vs_other")
int_top <- top_model("Core_CAF_interaction")
tac_path <- top_enrich("TAC_high_vs_other")
int_path <- top_enrich("Core_CAF_interaction")

report <- c(
  "# TAC_high Data-Driven Transcriptome Program",
  "",
  "This module tested whether TAC_high has a data-driven transcriptomic program beyond the pre-specified score panels.",
  "",
  "## Models",
  "",
  "- `TAC_high_vs_other`: limma differential expression within each bulk cohort, followed by signed Stouffer meta-analysis.",
  "- `Core_CAF_interaction`: limma model for `core_high * caf_high`; the interaction term asks whether the TAC_high quadrant exceeds additive core-high and CAF-high components.",
  "",
  "## Key Results",
  "",
  sprintf("Matched expression/state matrix: %s genes across %s tumour samples.", nrow(expr), ncol(expr)),
  sprintf("TAC_high vs other completed in %s cohorts; core-by-CAF interaction completed in %s cohorts.",
          sum(model_status$model == "TAC_high_vs_other" & model_status$status == "completed"),
          sum(model_status$model == "Core_CAF_interaction" & model_status$status == "completed")),
  sprintf("Top TAC_high-vs-other meta gene: `%s` (combined z=%s, meta FDR=%s).",
          tac_top$gene, fmt(tac_top$combined_z), fmt_p(tac_top$meta_FDR)),
  sprintf("Top core-by-CAF interaction gene: `%s` (combined z=%s, meta FDR=%s).",
          int_top$gene, fmt(int_top$combined_z), fmt_p(int_top$meta_FDR)),
  sprintf("Top positive TAC_high-vs-other pathway: `%s` (delta mean z=%s, FDR=%s).",
          tac_path$gene_set, fmt(tac_path$delta_mean_z), fmt_p(tac_path$FDR)),
  sprintf("Top positive interaction pathway: `%s` (delta mean z=%s, FDR=%s).",
          int_path$gene_set, fmt(int_path$delta_mean_z), fmt_p(int_path$FDR)),
  "",
  "## Interpretation Boundary",
  "",
  "This is a transcriptome-level association layer. It can support a data-driven stress-ecology program if pathway and gene-level results align, but it does not prove TMEM158 causality, drug resistance, protein-level UPR activation, or clinical treatment response."
)
writeLines(report, con = file.path(branch_root, "07_manuscript", "tmem158_tac_high_transcriptome_program_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
new_index <- data.frame(
  result = c(
    "tac_high_transcriptome_status",
    "tac_high_per_cohort_limma",
    "tac_high_meta_differential_genes",
    "tac_high_geneset_enrichment",
    "figure13_tac_high_transcriptome_programs",
    "figure14_tac_high_interaction_gene_heatmap",
    "tac_high_transcriptome_update"
  ),
  path = c(
    "04_results/qc/tmem158_tac_high_transcriptome_program_status.csv",
    "04_results/transcriptome/tmem158_tac_high_per_cohort_limma.csv",
    "04_results/transcriptome/tmem158_tac_high_meta_differential_genes.csv",
    "04_results/transcriptome/tmem158_tac_high_geneset_enrichment.csv",
    "05_figures/figure13_tac_high_transcriptome_programs.png",
    "05_figures/figure14_tac_high_interaction_gene_heatmap.png",
    "07_manuscript/tmem158_tac_high_transcriptome_program_update.md"
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

write_log("TAC_high transcriptome program module completed")
