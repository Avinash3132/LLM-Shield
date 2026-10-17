import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge conditional class names and resolve Tailwind conflicts.
 * Standard shadcn/ui helper — every component in `components/ui` depends on it.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
