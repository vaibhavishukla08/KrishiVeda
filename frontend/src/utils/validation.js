// Client-side checks mirror the backend rules so farmers get instant feedback.
// The backend validates again — never rely on the browser alone.

export const MAX_IMAGE_MB = 5;
export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

/** Returns an error key (for i18n) or null if the file looks acceptable. */
export function validateImageFile(file) {
  if (!file) return "err_no_file";
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) return "err_file_type";
  if (file.size === 0) return "err_file_empty";
  if (file.size > MAX_IMAGE_MB * 1024 * 1024) return "err_file_size";
  return null;
}

// Allowed ranges for the crop recommendation form (same as the API)
export const CROP_FIELDS = [
  { key: "N", min: 0, max: 300, step: 1, unit: "kg/ha", example: 90 },
  { key: "P", min: 0, max: 300, step: 1, unit: "kg/ha", example: 42 },
  { key: "K", min: 0, max: 400, step: 1, unit: "kg/ha", example: 43 },
  { key: "ph", min: 3, max: 10, step: 0.1, unit: "", example: 6.5 },
  { key: "temperature", min: -10, max: 55, step: 0.1, unit: "°C", example: 21 },
  { key: "humidity", min: 0, max: 100, step: 1, unit: "%", example: 82 },
  { key: "rainfall", min: 0, max: 5000, step: 1, unit: "mm", example: 203 },
];

/** Returns {field: errorKey} for invalid or missing numeric inputs. */
export function validateCropInputs(values) {
  const errors = {};
  for (const f of CROP_FIELDS) {
    const raw = values[f.key];
    if (raw === "" || raw === undefined || raw === null) {
      errors[f.key] = "err_required";
      continue;
    }
    const n = Number(raw);
    if (!Number.isFinite(n)) errors[f.key] = "err_number";
    else if (n < f.min || n > f.max) errors[f.key] = "err_range";
  }
  return errors;
}

export function validatePhone(phone) {
  return !phone || /^[6-9]\d{9}$/.test(phone);
}
