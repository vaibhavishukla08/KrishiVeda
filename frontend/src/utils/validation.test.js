import { describe, expect, it } from "vitest";
import { CROP_FIELDS, validateCropInputs, validateImageFile, validatePhone } from "./validation";
import { STRINGS } from "../i18n/strings";

const file = (type, size) => ({ type, size });

describe("validateImageFile", () => {
  it("accepts JPG, PNG and WEBP under 5 MB", () => {
    expect(validateImageFile(file("image/jpeg", 200_000))).toBeNull();
    expect(validateImageFile(file("image/png", 1_000))).toBeNull();
    expect(validateImageFile(file("image/webp", 5 * 1024 * 1024))).toBeNull();
  });
  it("rejects missing, wrong type, empty and oversized files", () => {
    expect(validateImageFile(null)).toBe("err_no_file");
    expect(validateImageFile(file("application/pdf", 1000))).toBe("err_file_type");
    expect(validateImageFile(file("image/jpeg", 0))).toBe("err_file_empty");
    expect(validateImageFile(file("image/jpeg", 5 * 1024 * 1024 + 1))).toBe("err_file_size");
  });
});

describe("validateCropInputs", () => {
  const valid = Object.fromEntries(CROP_FIELDS.map((f) => [f.key, String(f.example)]));
  it("accepts the example values", () => {
    expect(validateCropInputs(valid)).toEqual({});
  });
  it("flags missing, non-numeric and out-of-range values", () => {
    const errors = validateCropInputs({ ...valid, N: "", ph: "abc", humidity: "150" });
    expect(errors).toEqual({ N: "err_required", ph: "err_number", humidity: "err_range" });
  });
});

describe("validatePhone", () => {
  it("allows empty or valid Indian mobile numbers", () => {
    expect(validatePhone("")).toBe(true);
    expect(validatePhone("9876543210")).toBe(true);
    expect(validatePhone("1234567890")).toBe(false);
    expect(validatePhone("98765")).toBe(false);
  });
});

describe("i18n", () => {
  it("has the same keys in English and Hindi", () => {
    expect(Object.keys(STRINGS.hi).sort()).toEqual(Object.keys(STRINGS.en).sort());
  });
});
