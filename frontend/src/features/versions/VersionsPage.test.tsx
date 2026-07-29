import { render, screen } from "@testing-library/react";

import { listArtifactVersions } from "../../api/client";
import { VersionsPage } from "./VersionsPage";

vi.mock("../../api/client", () => ({
  listArtifactVersions: vi.fn(),
}));

const mockedListArtifactVersions = vi.mocked(listArtifactVersions);

describe("VersionsPage", () => {
  beforeEach(() => {
    mockedListArtifactVersions.mockReset();
  });

  it("renders approval status and safe PR links", async () => {
    mockedListArtifactVersions.mockResolvedValue([
      {
        id: "artifact-1",
        system_id: "demo",
        commit_sha: "abcdef123456",
        phase: "as-is",
        tag: null,
        author_type: "agent",
        run_id: "as-is-job-1",
        approval_status: "approved",
        approved_by: "mo-sameh1",
        approved_at: "2026-07-29T12:00:00Z",
        pr_number: 7,
        pr_url: "https://github.com/example/repo/pull/7",
        created_at: "2026-07-29T11:00:00Z",
      },
    ]);

    render(<VersionsPage systemId="demo" />);

    expect(await screen.findByText("approved")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /pr 7/i });
    expect(link).toHaveAttribute("href", "https://github.com/example/repo/pull/7");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noreferrer");
  });
});
