import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportProductPage from "./ImportProductPage";

describe("ImportProductPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const fillRequiredFields = () => {
    fireEvent.change(screen.getByLabelText(/Source URL/i), {
      target: { value: "https://example.com/item/1" },
    });
    fireEvent.change(screen.getByLabelText(/Source Site/i), {
      target: { value: "TAOBAO" },
    });
  };

  it("shows a success status when the import succeeds", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, options: [] }),
    } as Response);

    render(<ImportProductPage />);
    fillRequiredFields();
    fireEvent.click(screen.getByText(/Submit/i));

    await waitFor(() => {
      expect(
        screen.getByText(/Imported and queued for localization/i)
      ).toBeInTheDocument();
    });
  });

  it("surfaces scrape failures with a clear retry prompt", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "상품 정보를 불러오지 못했습니다." }),
    } as Response);

    render(<ImportProductPage />);
    fillRequiredFields();
    fireEvent.click(screen.getByText(/Submit/i));

    await waitFor(() => {
      expect(
        screen.getByText(/URL을 확인하거나 잠시 후 다시 시도/i)
      ).toBeInTheDocument();
    });
  });
});
