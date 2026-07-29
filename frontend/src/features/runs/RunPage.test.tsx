import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { getJob, triggerIngestion } from "../../api/client";
import { RunPage } from "./RunPage";

vi.mock("../../api/client", () => ({
  getJob: vi.fn(),
  triggerIngestion: vi.fn(),
}));

const mockedGetJob = vi.mocked(getJob);
const mockedTriggerIngestion = vi.mocked(triggerIngestion);

describe("RunPage", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_JOB_POLLING_MS", "10");
    window.localStorage.clear();
    mockedGetJob.mockReset();
    mockedTriggerIngestion.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("triggers ingestion and polls until the job succeeds", async () => {
    mockedTriggerIngestion.mockResolvedValue({
      job_id: "job-1",
      system_id: "demo",
      phase: "as-is",
      status: "queued",
      run_id: "as-is-job-1",
    });
    mockedGetJob
      .mockResolvedValueOnce({
        id: "job-1",
        system_id: "demo",
        phase: "as-is",
        status: "running",
        run_id: "as-is-job-1",
        error_message: null,
        started_at: null,
        finished_at: null,
      })
      .mockResolvedValue({
        id: "job-1",
        system_id: "demo",
        phase: "as-is",
        status: "succeeded",
        run_id: "as-is-job-1",
        error_message: null,
        started_at: null,
        finished_at: "2026-07-29T12:00:00Z",
      });

    render(<RunPage systemId="demo" />);
    await userEvent.click(screen.getByRole("button", { name: /run/i }));

    expect(mockedTriggerIngestion).toHaveBeenCalledWith("demo", undefined);
    expect(window.localStorage.getItem("mvp-phase1:last-job:demo")).toBe("job-1");

    await waitFor(() => expect(mockedGetJob).toHaveBeenCalledTimes(1));

    await waitFor(() => expect(screen.getAllByText("succeeded").length).toBeGreaterThan(0));
  });

  it("renders failed job error messages", async () => {
    window.localStorage.setItem("mvp-phase1:last-job:demo", "job-2");
    mockedGetJob.mockResolvedValue({
      id: "job-2",
      system_id: "demo",
      phase: "as-is",
      status: "failed",
      run_id: "as-is-job-2",
      error_message: "Validation failed",
      started_at: null,
      finished_at: null,
    });

    render(<RunPage systemId="demo" />);

    expect(await screen.findByText("Validation failed")).toBeInTheDocument();
  });
});
