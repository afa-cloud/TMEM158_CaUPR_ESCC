#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
log_file <- file.path(branch_root, "logs", "tmem158_tac_high_specificity.log")
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

signed_stouffer <- function(tab, effect_col = "delta") {
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

plot_save <- function(p, stem, width = 8, height = 5) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300)
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height)
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height)
  TRUE
}

write_log("Reading TAC_high state score matrix")

state_scores <- read_csv(file.path(branch_root, "02_data", "processed", "tmem158_tumor_ecology_state_scores.csv"))
required <- c("dataset", "ecology_subtype", "core_high", "caf_high",
              "Proteostasis_score", "Survival_score", "Drug_efflux_score")
missing <- setdiff(required, names(state_scores))
if (length(missing) > 0) stop("Missing required columns: ", paste(missing, collapse = ", "))

outcomes <- c("Proteostasis_score", "Survival_score", "Drug_efflux_score")
for (metric in outcomes) {
  state_scores[[paste0("z_", metric)]] <- ave(state_scores[[metric]], state_scores$dataset, FUN = zscore)
}

state_scores$tac_high_binary <- state_scores$ecology_subtype == "TAC_high"
state_scores$core_high_binary <- as.logical(state_scores$core_high)
state_scores$caf_high_binary <- as.logical(state_scores$caf_high)

component_tests <- data.frame()
component_pairs <- list(
  c("TAC_high", "TAC_low"),
  c("TAC_high", "Axis_only"),
  c("TAC_high", "CAF_only"),
  c("Axis_only", "CAF_only")
)

for (ds in sort(unique(state_scores$dataset))) {
  d <- state_scores[state_scores$dataset == ds, ]
  for (metric in outcomes) {
    zmetric <- paste0("z_", metric)
    for (pair in component_pairs) {
      dd <- d[d$ecology_subtype %in% pair & is.finite(d[[zmetric]]), ]
      group <- factor(dd$ecology_subtype, levels = pair)
      n_a <- sum(group == pair[1])
      n_b <- sum(group == pair[2])
      p <- NA_real_
      if (n_a >= 3 && n_b >= 3) {
        p <- suppressWarnings(stats::wilcox.test(dd[[zmetric]] ~ group)$p.value)
      }
      med_a <- ifelse(n_a > 0, stats::median(dd[[zmetric]][group == pair[1]], na.rm = TRUE), NA_real_)
      med_b <- ifelse(n_b > 0, stats::median(dd[[zmetric]][group == pair[2]], na.rm = TRUE), NA_real_)
      component_tests <- rbind(component_tests, data.frame(
        dataset = ds,
        metric = metric,
        contrast = paste(pair, collapse = "_vs_"),
        n_a = n_a,
        n_b = n_b,
        n_total = n_a + n_b,
        median_a = med_a,
        median_b = med_b,
        delta = med_a - med_b,
        p.value = p
      ))
    }
  }
}

component_tests$FDR <- stats::p.adjust(component_tests$p.value, method = "BH")
component_tests$direction <- ifelse(component_tests$delta > 0, "higher_in_first_state", "lower_in_first_state")
write_csv(component_tests, file.path(branch_root, "04_results", "validation", "tmem158_tac_high_component_specificity_tests.csv"))

component_meta <- do.call(rbind, lapply(split(component_tests, paste(component_tests$metric, component_tests$contrast, sep = "||")), function(tab) {
  ans <- signed_stouffer(tab)
  parts <- strsplit(unique(paste(tab$metric, tab$contrast, sep = "||")), "\\|\\|")[[1]]
  data.frame(metric = parts[1], contrast = parts[2], ans)
}))
component_meta$meta_FDR <- stats::p.adjust(component_meta$meta_p, method = "BH")
write_csv(component_meta, file.path(branch_root, "04_results", "validation", "tmem158_tac_high_component_specificity_meta.csv"))

interaction_rows <- data.frame()
for (ds in sort(unique(state_scores$dataset))) {
  d <- state_scores[state_scores$dataset == ds, ]
  for (metric in outcomes) {
    zmetric <- paste0("z_", metric)
    dd <- d[is.finite(d[[zmetric]]) & !is.na(d$core_high_binary) & !is.na(d$caf_high_binary), ]
    if (nrow(dd) < 12 || length(unique(dd$core_high_binary)) < 2 || length(unique(dd$caf_high_binary)) < 2) next
    fit <- stats::lm(dd[[zmetric]] ~ dd$core_high_binary * dd$caf_high_binary)
    coefs <- summary(fit)$coefficients
    term <- "dd$core_high_binaryTRUE:dd$caf_high_binaryTRUE"
    interaction_rows <- rbind(interaction_rows, data.frame(
      dataset = ds,
      metric = metric,
      n = nrow(dd),
      interaction_beta = ifelse(term %in% rownames(coefs), coefs[term, "Estimate"], NA_real_),
      interaction_p = ifelse(term %in% rownames(coefs), coefs[term, "Pr(>|t|)"], NA_real_),
      model_adj_r2 = summary(fit)$adj.r.squared
    ))
  }
}
interaction_rows$interaction_FDR <- stats::p.adjust(interaction_rows$interaction_p, method = "BH")
write_csv(interaction_rows, file.path(branch_root, "04_results", "validation", "tmem158_tac_high_interaction_models.csv"))

set.seed(1582026)
B <- 2000
permutation_rows <- data.frame()
null_rows <- data.frame()
for (metric in outcomes) {
  zmetric <- paste0("z_", metric)
  obs_by_ds <- data.frame()
  for (ds in sort(unique(state_scores$dataset))) {
    d <- state_scores[state_scores$dataset == ds & is.finite(state_scores[[zmetric]]), ]
    n_tac <- sum(d$tac_high_binary, na.rm = TRUE)
    n_other <- nrow(d) - n_tac
    if (n_tac < 3 || n_other < 3) next
    obs_delta <- stats::median(d[[zmetric]][d$tac_high_binary], na.rm = TRUE) -
      stats::median(d[[zmetric]][!d$tac_high_binary], na.rm = TRUE)
    obs_by_ds <- rbind(obs_by_ds, data.frame(dataset = ds, n_total = nrow(d), n_tac = n_tac, delta = obs_delta))
  }
  if (nrow(obs_by_ds) == 0) next
  weights <- sqrt(obs_by_ds$n_total)
  observed_meta_delta <- sum(weights * obs_by_ds$delta) / sum(weights)
  perm_meta <- rep(NA_real_, B)
  for (b in seq_len(B)) {
    deltas <- rep(NA_real_, nrow(obs_by_ds))
    for (i in seq_len(nrow(obs_by_ds))) {
      ds <- obs_by_ds$dataset[i]
      d <- state_scores[state_scores$dataset == ds & is.finite(state_scores[[zmetric]]), ]
      idx <- sample(seq_len(nrow(d)), obs_by_ds$n_tac[i], replace = FALSE)
      deltas[i] <- stats::median(d[[zmetric]][idx], na.rm = TRUE) -
        stats::median(d[[zmetric]][-idx], na.rm = TRUE)
    }
    perm_meta[b] <- sum(weights * deltas) / sum(weights)
  }
  empirical_two_sided <- (1 + sum(abs(perm_meta) >= abs(observed_meta_delta), na.rm = TRUE)) / (B + 1)
  empirical_greater <- (1 + sum(perm_meta >= observed_meta_delta, na.rm = TRUE)) / (B + 1)
  permutation_rows <- rbind(permutation_rows, data.frame(
    metric = metric,
    n_datasets = nrow(obs_by_ds),
    observed_meta_delta = observed_meta_delta,
    null_median = stats::median(perm_meta, na.rm = TRUE),
    null_q025 = stats::quantile(perm_meta, 0.025, na.rm = TRUE),
    null_q975 = stats::quantile(perm_meta, 0.975, na.rm = TRUE),
    empirical_two_sided_p = empirical_two_sided,
    empirical_greater_p = empirical_greater,
    permutations = B
  ))
  null_rows <- rbind(null_rows, data.frame(metric = metric, permutation = seq_len(B), null_meta_delta = perm_meta))
}
permutation_rows$empirical_FDR <- stats::p.adjust(permutation_rows$empirical_two_sided_p, method = "BH")
write_csv(permutation_rows, file.path(branch_root, "04_results", "validation", "tmem158_tac_high_permutation_summary.csv"))
write_csv(null_rows, file.path(branch_root, "04_results", "validation", "tmem158_tac_high_permutation_null.csv"))

status <- data.frame(
  item = c("module_status", "bulk_datasets", "permutations_per_metric",
           "proteostasis_empirical_p", "survival_empirical_p", "drug_efflux_empirical_p",
           "proteostasis_observed_meta_delta", "survival_observed_meta_delta",
           "specificity_interpretation"),
  value = c(
    "completed",
    length(unique(state_scores$dataset)),
    B,
    permutation_rows$empirical_two_sided_p[match("Proteostasis_score", permutation_rows$metric)],
    permutation_rows$empirical_two_sided_p[match("Survival_score", permutation_rows$metric)],
    permutation_rows$empirical_two_sided_p[match("Drug_efflux_score", permutation_rows$metric)],
    permutation_rows$observed_meta_delta[match("Proteostasis_score", permutation_rows$metric)],
    permutation_rows$observed_meta_delta[match("Survival_score", permutation_rows$metric)],
    "TAC_high specificity evaluated against cohort-preserving random state labels and component-state contrasts"
  )
)
write_csv(status, file.path(branch_root, "04_results", "qc", "tmem158_tac_high_specificity_status.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  pdat <- permutation_rows
  pdat$metric_label <- gsub("_score", "", pdat$metric)
  y_min <- min(pdat$null_q025, pdat$observed_meta_delta, na.rm = TRUE) - 0.05
  y_max <- max(pdat$null_q975, pdat$observed_meta_delta, na.rm = TRUE) + 0.12
  p <- ggplot(pdat, aes(x = metric_label, y = observed_meta_delta)) +
    geom_hline(yintercept = 0, linewidth = 0.4, colour = "grey55") +
    geom_errorbar(aes(ymin = null_q025, ymax = null_q975), width = 0.16, colour = "grey35", linewidth = 0.8) +
    geom_point(size = 3.2, colour = "#1f6f78") +
    geom_text(aes(label = paste0("empirical P=", signif(empirical_two_sided_p, 2))),
              vjust = -0.9, size = 2.9) +
    coord_cartesian(ylim = c(y_min, y_max), clip = "off") +
    labs(
      title = "TAC_high state specificity against cohort-preserving random labels",
      x = NULL,
      y = "Weighted median delta, TAC_high minus other states"
    ) +
    theme_bw(base_size = 10) +
    theme(
      plot.title = element_text(face = "bold", size = 12.5),
      axis.title.y = element_text(size = 10),
      axis.text = element_text(size = 9),
      panel.grid.minor = element_blank(),
      axis.text.x = element_text(angle = 20, hjust = 1)
    )
  plot_save(p, file.path(branch_root, "05_figures", "figure12_tac_high_state_specificity"), width = 7.5, height = 4.8)
}

fmt_metric <- function(metric, col) {
  val <- permutation_rows[match(metric, permutation_rows$metric), col]
  ifelse(is.na(val), "NA", signif(val, 4))
}

report <- c(
  "# TAC_high State Specificity Update",
  "",
  "This module tested whether the TAC_high signal exceeds component-only and random-state explanations.",
  "",
  "## Outputs",
  "",
  "- `04_results/validation/tmem158_tac_high_component_specificity_tests.csv`",
  "- `04_results/validation/tmem158_tac_high_component_specificity_meta.csv`",
  "- `04_results/validation/tmem158_tac_high_interaction_models.csv`",
  "- `04_results/validation/tmem158_tac_high_permutation_summary.csv`",
  "- `05_figures/figure12_tac_high_state_specificity.*`",
  "",
  "## Key Interpretation",
  "",
  "TAC_high was evaluated against cohort-preserving random labels with the same TAC_high sample counts in each dataset. This provides a statistical specificity layer for the rule-defined state and helps distinguish TAC_high from a generic TMEM158-only or CAF-only biomarker framing.",
  "",
  sprintf("Permutation testing showed the strongest TAC_high specificity for `Drug_efflux_score` (observed weighted median delta=%s, empirical two-sided P=%s, empirical FDR=%s).",
          fmt_metric("Drug_efflux_score", "observed_meta_delta"),
          fmt_metric("Drug_efflux_score", "empirical_two_sided_p"),
          fmt_metric("Drug_efflux_score", "empirical_FDR")),
  "",
  sprintf("`Proteostasis_score` showed a directional but not FDR-confirmed specificity trend (delta=%s, empirical two-sided P=%s, empirical FDR=%s).",
          fmt_metric("Proteostasis_score", "observed_meta_delta"),
          fmt_metric("Proteostasis_score", "empirical_two_sided_p"),
          fmt_metric("Proteostasis_score", "empirical_FDR")),
  "",
  sprintf("`Survival_score` was not random-label specific (delta=%s, empirical two-sided P=%s).",
          fmt_metric("Survival_score", "observed_meta_delta"),
          fmt_metric("Survival_score", "empirical_two_sided_p")),
  "",
  "This updates the manuscript boundary: TAC_high is strongest as a transport/efflux-proteostasis transcriptional adaptation state. It should not be written as a validated clinical-survival subtype or therapy-resistance mechanism.",
  "",
  "The module remains association-based and does not prove causal TMEM158 activity."
)
writeLines(report, con = file.path(branch_root, "07_manuscript", "tmem158_tac_high_specificity_update.md"))

index_path <- file.path(branch_root, "04_results", "result_index.csv")
new_index <- data.frame(
  result = c(
    "tac_high_specificity_status",
    "tac_high_permutation_summary",
    "tac_high_component_specificity_meta",
    "tac_high_interaction_models",
    "figure12_tac_high_specificity",
    "manuscript_draft",
    "submission_package",
    "formal_duplication_gate",
    "pubmed_pmc_duplication_counts",
    "pmc_fulltext_term_scan",
    "manual_download_manifest"
  ),
  path = c(
    "04_results/qc/tmem158_tac_high_specificity_status.csv",
    "04_results/validation/tmem158_tac_high_permutation_summary.csv",
    "04_results/validation/tmem158_tac_high_component_specificity_meta.csv",
    "04_results/validation/tmem158_tac_high_interaction_models.csv",
    "05_figures/figure12_tac_high_state_specificity.png",
    "07_manuscript/manuscript.md",
    "07_manuscript/submission_package.md",
    "01_literature/tmem158_formal_duplication_gate_2026-06-19.md",
    "01_literature/tmem158_pubmed_pmc_duplication_counts.csv",
    "01_literature/tmem158_pmc_fulltext_term_scan.csv",
    "01_literature/manual_download_manifest.csv"
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

write_log("TAC_high specificity module completed")
