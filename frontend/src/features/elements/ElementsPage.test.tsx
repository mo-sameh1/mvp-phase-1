import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BrowserRouter } from "../../app/router";
import { listElements } from "../../api/client";
import { ElementsPage } from "./ElementsPage";

vi.mock("../../api/client", () => ({
  listElements: vi.fn(),
}));

const mockedListElements = vi.mocked(listElements);

describe("ElementsPage", () => {
  beforeEach(() => {
    mockedListElements.mockReset();
  });

  it("groups model elements by layer and filters by search", async () => {
    mockedListElements.mockResolvedValue([
      modelElement({ id: "order-service", layer: "application", name: "Order Service" }),
      modelElement({ id: "checkout-process", layer: "business", name: "Checkout Process" }),
    ]);

    render(
      <BrowserRouter>
        <ElementsPage systemId="demo" />
      </BrowserRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Application" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Business" })).toBeInTheDocument();
    expect(screen.getByText("Order Service")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Search model elements"), "checkout");

    expect(screen.queryByText("Order Service")).not.toBeInTheDocument();
    expect(screen.getByText("Checkout Process")).toBeInTheDocument();
  });
});

function modelElement(overrides: Partial<Awaited<ReturnType<typeof listElements>>[number]>) {
  return {
    id: "element",
    system_id: "demo",
    layer: "application",
    archimate_type: "Application Component",
    name: "Element",
    git_path: "systems/demo/as-is/application/element.json",
    current_commit: "abc123",
    updated_at: "2026-07-29T12:00:00Z",
    ...overrides,
  } as Awaited<ReturnType<typeof listElements>>[number];
}
