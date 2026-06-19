#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

branch_root <- normalizePath(file.path(getwd(), "TMEM158_CaUPR_ESCC"), mustWork = TRUE)
log_file <- file.path(branch_root, "logs", "tmem158_public_protein_context.log")
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

status_value <- function(status, key, default = "") {
  hit <- status$value[status$item == key]
  if (length(hit) == 0) default else as.character(hit[1])
}

summary_value <- function(summary, source, item, default = "") {
  hit <- summary$value[summary$source == source & summary$item == item]
  if (length(hit) == 0) default else as.character(hit[1])
}

truthy <- function(x) {
  as.character(x) %in% c("1", "TRUE", "true", "yes", "Yes")
}

update_result_index <- function(new_rows) {
  index_path <- file.path(branch_root, "04_results", "result_index.csv")
  old <- if (file.exists(index_path)) read.csv(index_path, check.names = FALSE) else data.frame(result = character(), path = character())
  old <- old[!old$result %in% new_rows$result, , drop = FALSE]
  write_csv(rbind(old, new_rows), index_path)
}

update_data_inventory <- function(new_rows) {
  path <- file.path(branch_root, "02_data", "data_inventory.csv")
  old <- if (file.exists(path)) read.csv(path, check.names = FALSE) else data.frame(source = character(), path = character(), reuse_role = character())
  old <- old[!old$source %in% new_rows$source, , drop = FALSE]
  write_csv(rbind(old, new_rows), path)
}

plot_save <- function(p, stem, width = 8.4, height = 5.2) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) return(FALSE)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(paste0(stem, ".png"), p, width = width, height = height, dpi = 300, bg = "white")
  ggplot2::ggsave(paste0(stem, ".pdf"), p, width = width, height = height, bg = "white")
  ggplot2::ggsave(paste0(stem, ".svg"), p, width = width, height = height, bg = "white")
  TRUE
}

write_log("Starting TMEM158 public protein/context module")

helper <- file.path(branch_root, "03_scripts", "Python", "download_tmem158_protein_context.py")
py <- Sys.which("python3")
if (!nzchar(py)) stop("python3 is required for official protein/context API download")
download_status <- system2(py, helper, stdout = log_file, stderr = log_file)
write_log(sprintf("download_tmem158_protein_context.py exit status: %s", download_status))
if (!identical(download_status, 0L)) quit(status = download_status)

summary <- safe_read_csv(file.path(branch_root, "04_results", "validation", "tmem158_public_protein_knowledgebase_summary.csv"))
localization <- safe_read_csv(file.path(branch_root, "04_results", "validation", "tmem158_uniprot_quickgo_localization.csv"), required = FALSE)
hpa_sc <- safe_read_csv(file.path(branch_root, "04_results", "validation", "tmem158_hpa_single_cell_context.csv"), required = FALSE)
status <- safe_read_csv(file.path(branch_root, "04_results", "qc", "tmem158_public_protein_context_status.csv"))

membrane_support <- truthy(status_value(status, "membrane_support", "0"))
er_support <- truthy(status_value(status, "er_direct_support", "0"))
hpa_subcell <- truthy(status_value(status, "hpa_subcellular_available", "0"))
hpa_ih <- truthy(status_value(status, "hpa_ih_approved", "0"))

evidence_cards <- data.frame(
  item = c(
    "Reviewed UniProt entry",
    "Membrane protein/topology support",
    "HPA predicted membrane protein class",
    "Public antibody/IHC context",
    "Direct ER localization",
    "HPA subcellular IF location",
    "ESCC-specific protein validation"
  ),
  score = c(
    ifelse(grepl("reviewed", summary_value(summary, "UniProt", "reviewed_accession", ""), ignore.case = TRUE) ||
             nzchar(summary_value(summary, "UniProt", "reviewed_accession", "")), 1, 0),
    ifelse(membrane_support, 1, -0.2),
    ifelse(grepl("membrane", summary_value(summary, "HPA", "protein_class", ""), ignore.case = TRUE), 1, -0.2),
    ifelse(hpa_ih, 0.6, -0.2),
    ifelse(er_support, 0.7, -0.8),
    ifelse(hpa_subcell, 0.5, -0.7),
    -1
  ),
  boundary_call = c(
    "support",
    ifelse(membrane_support, "support", "weak_or_missing"),
    ifelse(grepl("membrane", summary_value(summary, "HPA", "protein_class", ""), ignore.case = TRUE), "support", "weak_or_missing"),
    ifelse(hpa_ih, "context", "weak_or_missing"),
    ifelse(er_support, "context", "boundary"),
    ifelse(hpa_subcell, "context", "boundary"),
    "boundary"
  ),
  note = c(
    paste0(summary_value(summary, "UniProt", "reviewed_accession"), " / ", summary_value(summary, "UniProt", "protein_name")),
    paste0(summary_value(summary, "UniProt", "subcellular_location"), "; ", summary_value(summary, "UniProt", "topology")),
    summary_value(summary, "HPA", "protein_class"),
    paste0(summary_value(summary, "HPA", "antibody"), "; ", summary$evidence_level[summary$source == "HPA" & summary$item == "antibody"][1]),
    ifelse(er_support, "ER/endomembrane term found", "No direct ER term in retrieved UniProt/QuickGO localization"),
    ifelse(hpa_subcell, summary_value(summary, "HPA", "subcellular_location"), "HPA subcellular IF not available"),
    "No public ESCC-specific TMEM158 protein/localization experiment is created by this workflow"
  ),
  stringsAsFactors = FALSE
)
write_csv(evidence_cards, file.path(branch_root, "04_results", "validation", "tmem158_public_protein_evidence_cards.csv"))

if (!is.null(hpa_sc) && nrow(hpa_sc) > 0) {
  top_sc <- head(hpa_sc[order(-as.numeric(hpa_sc$nCPM)), ], 8)
} else {
  top_sc <- data.frame(rank = integer(), cell_type = character(), nCPM = numeric())
}
write_csv(top_sc, file.path(branch_root, "04_results", "validation", "tmem158_hpa_top_single_cell_context.csv"))

if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  plot_cards <- evidence_cards
  plot_cards$item <- factor(plot_cards$item, levels = plot_cards$item[order(plot_cards$score)])
  p11 <- ggplot(plot_cards, aes(x = item, y = score, fill = boundary_call)) +
    geom_hline(yintercept = 0, linewidth = 0.35, color = "grey55") +
    geom_col(width = 0.68, color = "white", linewidth = 0.25) +
    coord_flip() +
    scale_fill_manual(values = c(
      support = "#2E7D60",
      context = "#7B6F4A",
      weak_or_missing = "#BCA35B",
      boundary = "#A6423A"
    ), drop = FALSE) +
    scale_y_continuous(limits = c(-1.1, 1.1), breaks = c(-1, -0.5, 0, 0.5, 1)) +
    labs(
      title = "TMEM158 public protein and localization context",
      subtitle = "Official UniProt, QuickGO and HPA evidence; database-level context, not new protein validation",
      x = NULL,
      y = "Evidence direction",
      fill = "Call"
    ) +
    theme_classic(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold"),
      plot.subtitle = element_text(size = 9),
      legend.position = "bottom"
    )
  plot_save(p11, file.path(branch_root, "05_figures", "figure11_tmem158_public_protein_context"))
}

module_status_final <- data.frame(
  item = c("module_status_final", "figure11_generated", "report_generated", "main_interpretation"),
  value = c(
    status_value(status, "module_status", "partial_completed"),
    file.exists(file.path(branch_root, "05_figures", "figure11_tmem158_public_protein_context.png")),
    TRUE,
    "membrane_protein_plausibility_and_antibody_context_not_er_or_escc_protein_validation"
  ),
  stringsAsFactors = FALSE
)
status_out <- rbind(status, module_status_final)
write_csv(status_out, file.path(branch_root, "04_results", "qc", "tmem158_public_protein_context_status.csv"))

accession <- summary_value(summary, "UniProt", "reviewed_accession", "NA")
protein_name <- summary_value(summary, "UniProt", "protein_name", "NA")
location <- summary_value(summary, "UniProt", "subcellular_location", "NA")
topology <- summary_value(summary, "UniProt", "topology", "NA")
hpa_class <- summary_value(summary, "HPA", "protein_class", "NA")
hpa_antibody <- summary_value(summary, "HPA", "antibody", "NA")
hpa_subcell_value <- summary_value(summary, "HPA", "subcellular_location", "NA")
hpa_protein_dist <- summary_value(summary, "HPA", "protein_tissue_distribution", "NA")
hpa_sc_line <- if (nrow(top_sc) > 0) {
  paste(sprintf("- %s: %s nCPM", top_sc$cell_type, top_sc$nCPM), collapse = "\n")
} else {
  "- No HPA single-cell entries were available."
}
go_line <- if (!is.null(localization) && nrow(localization) > 0) {
  paste(unique(paste0(localization$source, " ", localization$term_id, " ", localization$term_name, " [", localization$evidence, "]")), collapse = "; ")
} else {
  "No UniProt/QuickGO cellular-component rows were retrieved."
}

report <- c(
  "# TMEM158 public protein and localization context",
  "",
  "## Purpose",
  "",
  "This module adds official public protein/context evidence for TMEM158 after the TAC_high state analysis. It is intended to support biological plausibility and assayability, not to create new ESCC protein validation.",
  "",
  "## Data used",
  "",
  "- UniProt REST query: `gene_exact:TMEM158 AND organism_id:9606`.",
  "- QuickGO cellular-component annotations for the retrieved UniProt accession.",
  "- Human Protein Atlas TMEM158 search and individual ENSG entry.",
  "",
  "## Main findings",
  "",
  paste0("- UniProt reviewed accession: ", accession, " (", protein_name, ")."),
  paste0("- UniProt subcellular location/topology: ", location, "; ", topology, "."),
  paste0("- UniProt/QuickGO cellular-component terms: ", go_line),
  paste0("- HPA protein class: ", hpa_class, "."),
  paste0("- HPA public antibody/IHC context: ", hpa_antibody, "."),
  paste0("- HPA protein tissue distribution: ", hpa_protein_dist, "."),
  paste0("- HPA subcellular IF main location: ", ifelse(nzchar(hpa_subcell_value), hpa_subcell_value, "not available"), "."),
  "",
  "## HPA single-cell RNA context",
  "",
  hpa_sc_line,
  "",
  "## Interpretation boundary",
  "",
  "This layer supports TMEM158 as a public, reviewed transmembrane-protein candidate with HPA antibody/IHC context. It does not show ESCC-specific TMEM158 protein overexpression, direct ER localization, Ca2+ flux, UPR activation, CAF causality, immune suppression or treatment resistance. In the manuscript, it should be placed as a database-level protein plausibility and limitation layer.",
  "",
  "## Output files",
  "",
  "- `04_results/validation/tmem158_public_protein_knowledgebase_summary.csv`",
  "- `04_results/validation/tmem158_uniprot_quickgo_localization.csv`",
  "- `04_results/validation/tmem158_hpa_context_summary.csv`",
  "- `04_results/validation/tmem158_public_protein_evidence_cards.csv`",
  "- `04_results/qc/tmem158_public_protein_context_status.csv`",
  "- `05_figures/figure11_tmem158_public_protein_context.png/.pdf/.svg`"
)
writeLines(report, file.path(branch_root, "07_manuscript", "tmem158_public_protein_context_update.md"))

update_result_index(data.frame(
  result = c(
    "tmem158_public_protein_summary",
    "tmem158_public_protein_localization",
    "tmem158_hpa_single_cell_context",
    "tmem158_public_protein_status"
  ),
  path = c(
    "04_results/validation/tmem158_public_protein_knowledgebase_summary.csv",
    "04_results/validation/tmem158_uniprot_quickgo_localization.csv",
    "04_results/validation/tmem158_hpa_single_cell_context.csv",
    "04_results/qc/tmem158_public_protein_context_status.csv"
  ),
  stringsAsFactors = FALSE
))

update_data_inventory(data.frame(
  source = c("UniProt/QuickGO TMEM158 protein context", "Human Protein Atlas TMEM158 context"),
  path = c(
    file.path(branch_root, "02_data", "raw", "protein_context", "TMEM158_uniprot_search.json"),
    file.path(branch_root, "02_data", "raw", "protein_context")
  ),
  reuse_role = c("public protein identity and localization terms", "public protein/RNA/antibody context")
))

write_log("TMEM158 public protein/context module completed")
