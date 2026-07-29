import type { Layer, ModelElementIndex } from "../../api/types";
import { LAYERS } from "../../api/types";

export const LAYER_LABELS: Record<Layer, string> = {
  motivation: "Motivation",
  strategy: "Strategy",
  business: "Business",
  application: "Application",
  technology: "Technology",
};

export function groupElementsByLayer(elements: ModelElementIndex[]): Record<Layer, ModelElementIndex[]> {
  return LAYERS.reduce(
    (grouped, layer) => ({
      ...grouped,
      [layer]: elements.filter((element) => element.layer === layer),
    }),
    {} as Record<Layer, ModelElementIndex[]>,
  );
}
