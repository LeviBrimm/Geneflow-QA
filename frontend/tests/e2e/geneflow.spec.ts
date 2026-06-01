import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/register", async (route) => {
    await route.fulfill({
      json: { access_token: "test-token", token_type: "bearer", email: "qa@example.com" },
    });
  });
  await page.route("**/api/variants/analyze", async (route) => {
    await route.fulfill({
      status: 202,
      json: { query_id: 12, job_id: "job-12", status: "queued" },
    });
  });
  await page.route("**/api/jobs/job-12", async (route) => {
    await route.fulfill({
      json: { job_id: "job-12", query_id: 12, status: "completed", error_message: null },
    });
  });
  await page.route("**/api/variants/12", async (route) => {
    await route.fulfill({
      json: {
        query_id: 12,
        raw_input: "BRCA1 c.5266dupC",
        status: "completed",
        created_at: "2026-06-01T20:00:00",
        job_id: "job-12",
        parsed: { gene: "BRCA1", notation: "c.5266dupC", variant_type: "frameshift", is_valid: true },
        reference: {
          gene_full_name: "BRCA1 DNA repair associated",
          gene_description: "BRCA1 is involved in DNA repair and genome stability.",
          rsid: "rs80357906",
          significance: "Pathogenic",
          condition: "Hereditary breast and ovarian cancer syndrome",
          allele_frequency: 0.00003,
          summary: "A duplication in BRCA1 that disrupts the reading frame.",
          position: 5266,
          domain: "BRCT domain",
        },
        explanations: {
          general: "General guarded explanation. Educational only. Not medical advice.",
          technical: "Technical guarded explanation. Educational only. Not medical advice.",
          model_used: "mock-explainer-v1",
        },
        similar_variants: [
          {
            variant_id: 2,
            gene: "TP53",
            hgvs: "p.R175H",
            significance: "Pathogenic",
            condition: "Li-Fraumeni syndrome",
            similarity_score: 0.82,
          },
        ],
      },
    });
  });
  await page.route("**/api/variants/history", async (route) => {
    await route.fulfill({
      json: [
        {
          query_id: 12,
          raw_input: "BRCA1 c.5266dupC",
          status: "completed",
          created_at: "2026-06-01T20:00:00",
          job_id: "job-12",
        },
      ],
    });
  });
});

test("user can register, submit a variant, view results, and open history", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page.getByLabel(/variant input/i)).toBeVisible();
  await page.getByRole("button", { name: /start analysis/i }).click();
  await expect(page.getByRole("status")).toContainText(/Analysis status/i);
  await expect(page.getByRole("heading", { name: "BRCA1 c.5266dupC" })).toBeVisible();
  await expect(page.getByText("Pathogenic")).toBeVisible();
  await expect(page.getByText("General guarded explanation")).toBeVisible();
  await expect(page.getByText("TP53 p.R175H")).toBeVisible();

  await page.getByRole("link", { name: /history/i }).click();
  await expect(page.getByRole("heading", { name: "Query History" })).toBeVisible();
  await expect(page.getByText("BRCA1 c.5266dupC")).toBeVisible();
});

test("invalid variant submission surfaces API validation errors", async ({ page }) => {
  await page.route("**/api/variants/analyze", async (route) => {
    await route.fulfill({ status: 422, json: { detail: "Unable to parse variant." } });
  });

  await page.goto("/");
  await page.getByRole("button", { name: /create account/i }).click();
  await page.getByLabel(/variant input/i).fill("bad input");
  await page.getByRole("button", { name: /start analysis/i }).click();

  await expect(page.getByText("Unable to parse variant.")).toBeVisible();
});
