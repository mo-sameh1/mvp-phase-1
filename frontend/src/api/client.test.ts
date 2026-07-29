import { ApiError, getJob, requestJson, triggerIngestion } from "./client";

describe("api client", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_BASE_PATH", "/api");
    vi.stubEnv("VITE_API_KEY", "test-key");
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("sends the configured API key and parses JSON responses", async () => {
    const fetchSpy = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "job-1", status: "running" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const result = await getJob("job-1");

    expect(result.status).toBe("running");
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/jobs/job-1",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ "X-API-Key": "test-key" }),
      }),
    );
  });

  it("posts ingestion requests with optional evidence path", async () => {
    const fetchSpy = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ job_id: "job-1", status: "queued" }), { status: 202 }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    await triggerIngestion("demo", "/evidence/custom");

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/systems/demo/ingest",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ evidence_path: "/evidence/custom" }),
      }),
    );
  });

  it("surfaces backend error details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Invalid API key" }), {
          status: 401,
          statusText: "Unauthorized",
        }),
      ),
    );

    await expect(requestJson("/jobs/job-1")).rejects.toEqual(new ApiError("Invalid API key", 401));
  });
});
