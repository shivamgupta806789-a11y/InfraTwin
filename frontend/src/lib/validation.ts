import { BuildingParams, BuildingFormErrors } from '../types/building';

export function validateBuildingParams(params: BuildingParams): { isValid: boolean; errors: BuildingFormErrors } {
  const errors: BuildingFormErrors = {};

  if (!params.width_m || isNaN(params.width_m) || params.width_m <= 0) {
    errors.width_m = 'Width must be a positive number greater than 0.';
  } else if (params.width_m > 200) {
    errors.width_m = 'Width exceeds maximum limit of 200m.';
  }

  if (!params.length_m || isNaN(params.length_m) || params.length_m <= 0) {
    errors.length_m = 'Length must be a positive number greater than 0.';
  } else if (params.length_m > 200) {
    errors.length_m = 'Length exceeds maximum limit of 200m.';
  }

  if (!params.floor_height_m || isNaN(params.floor_height_m) || params.floor_height_m < 1.5) {
    errors.floor_height_m = 'Floor height must be at least 1.5m.';
  } else if (params.floor_height_m > 10.0) {
    errors.floor_height_m = 'Floor height cannot exceed 10m.';
  }

  if (!params.floors || isNaN(params.floors) || !Number.isInteger(params.floors) || params.floors < 1) {
    errors.floors = 'Must have at least 1 floor.';
  } else if (params.floors > 50) {
    errors.floors = 'Maximum floor limit is 50.';
  }

  if (params.window_count === undefined || isNaN(params.window_count) || !Number.isInteger(params.window_count) || params.window_count < 0) {
    errors.window_count = 'Window count must be a non-negative integer.';
  } else if (params.window_count > 1000) {
    errors.window_count = 'Maximum window count is 1000.';
  }

  if (params.budget_inr === undefined || isNaN(params.budget_inr) || params.budget_inr < 0) {
    errors.budget_inr = 'Budget must be non-negative.';
  } else if (params.budget_inr > 1_000_000_000) {
    errors.budget_inr = 'Budget exceeds maximum calculation threshold (₹100 Cr).';
  }

  // Cross-field geometric check
  if (!errors.width_m && !errors.length_m && !errors.floor_height_m && !errors.floors && !errors.window_count) {
    const totalWallArea = 2 * (params.width_m + params.length_m) * (params.floors * params.floor_height_m);
    const estimatedWindowArea = params.window_count * 2.0;
    if (params.window_count > 0 && estimatedWindowArea > totalWallArea * 0.9) {
      errors.window_count = `Window count (${params.window_count}) exceeds plausible exterior wall area (${totalWallArea.toFixed(1)} m²).`;
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

export function formatINR(amount: number): string {
  if (isNaN(amount) || amount === null || amount === undefined) {
    return '₹ 0';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatArea(m2: number): string {
  return `${m2.toLocaleString('en-IN', { maximumFractionDigits: 1 })} m²`;
}
