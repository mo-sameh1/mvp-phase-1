import { render, screen } from "@testing-library/react";

import { getElementDetail } from "../../api/client";
import { BrowserRouter } from "../../app/router";
import { ElementDetailPage } from "./ElementDetailPage";

vi.mock("../../api/client", () => ({
  getElementDetail: vi.fn(),
}));

const mockedGetElementDetail = vi.mocked(getElementDetail);

describe("ElementDetailPage", () => {
  beforeEach(() => {
    mockedGetElementDetail.mockReset();
  });

  it("renders evidence citations, relationships, and model JSON link", async () => {
    mockedGetElementDetail.mockResolvedValue({
      id: "order-service",
      system_id: "demo",
      git_path: "systems/demo/as-is/application/order-service.json",
      current_commit: "abc123",
      model_json_url:
        "https://github.com/example/repo/blob/abc123/systems/demo/as-is/application/order-service.json",
      element: {
        id: "order-service",
        layer: "application",
        archimate_type: "Application Service",
        name: "Order Service",
        documentation: "Handles order submission.",
        confidence: "observed",
        evidence: [
          {
            source_type: "code",
            locator: "/evidence/code/openapi.yaml:1-8",
            excerpt: "POST /orders",
          },
        ],
        relationships: [
          {
            type: "Serving",
            target_id: "checkout-process",
            evidence: [
              {
                source_type: "integration",
                locator: "/evidence/integration/api-notes.md:3",
                excerpt: "Service supports checkout.",
              },
            ],
          },
        ],
      },
    });

    render(
      <BrowserRouter>
        <ElementDetailPage systemId="demo" elementId="order-service" />
      </BrowserRouter>,
    );

    expect(await screen.findByText("Handles order submission.")).toBeInTheDocument();
    expect(screen.getByText("/evidence/code/openapi.yaml:1-8")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open file/i })).toHaveAttribute(
      "href",
      expect.stringContaining("order-service.json"),
    );
    expect(screen.getByRole("link", { name: /serving checkout-process/i })).toHaveAttribute(
      "href",
      "/systems/demo/elements/checkout-process",
    );
  });
});
