from typing import List, Dict, Any, Tuple
from app.models.building import BuildingInput
from app.models.recommendations import (
    InterventionItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.cost_engine import CostEngine, INTERVENTION_CATALOG

class RecommendationEngine:
    @classmethod
    def evaluate_interventions(cls, request: RecommendationRequest) -> RecommendationResponse:
        building = request
        budget = building.budget_inr
        roof_area = building.width_m * building.length_m
        total_height = building.floors * building.floor_height_m
        wall_area = 2 * (building.width_m + building.length_m) * total_height
        window_wall_ratio = (building.window_count * 2.0) / wall_area if wall_area > 0 else 0.0

        all_items: List[InterventionItem] = []
        feasible_candidates: List[Tuple[float, InterventionItem]] = []
        warnings: List[str] = []
        missing_info: List[str] = [
            "Local climate zone / solar irradiance map (required for localized thermal load simulation)",
            "Utility electricity tariff / hourly load profile (required for dynamic bill savings)",
            "Roof structural load rating (required for structural engineer sign-off on ballast PV or screed)",
            "Local municipal solar net-metering regulations (DISCOM approval requirements)"
        ]

        if budget <= 0:
            warnings.append("Improvement budget is ₹0. No paid interventions can be recommended as feasible.")

        # Evaluate each catalog item
        for item_id, meta in INTERVENTION_CATALOG.items():
            is_eligible, ineligibility_reason, qty, qty_unit, cost = CostEngine.calculate_intervention_cost(
                item_id, building
            )

            fits_budget = (cost <= budget) if (is_eligible and budget > 0) else False

            # Calculate transparent scoring
            score = 0.0
            if is_eligible and fits_budget and budget > 0:
                # 1. Affordability factor (0 - 40 points)
                affordability = max(0.0, (1.0 - (cost / budget))) * 40.0
                
                # 2. Suitability factor (0 - 40 points)
                suitability = 25.0
                if item_id == "external_shading":
                    if window_wall_ratio > 0.20:
                        suitability = 38.0
                    elif building.window_count >= 8:
                        suitability = 34.0
                    else:
                        suitability = 26.0
                elif item_id == "reflective_roof":
                    # Greater relative benefit on low-rise buildings with high roof-to-volume ratio
                    suitability = 38.0 if building.floors <= 2 else 26.0
                elif item_id == "roof_insulation":
                    suitability = 35.0 if building.floors <= 2 else 24.0
                elif item_id == "solar_pv":
                    suitability = 37.0 if qty >= 3.0 else 30.0

                # 3. Evidence quality (0 - 20 points)
                evidence_quality = 18.0

                score = round(affordability + suitability + evidence_quality, 1)

            # Generate default explanation
            if not is_eligible:
                explanation = f"Ineligible for this building geometry: {ineligibility_reason}"
            elif budget <= 0:
                explanation = f"Requires an estimated capital expenditure of ₹{cost:,.0f}, which exceeds current zero budget."
            elif not fits_budget:
                shortfall = cost - budget
                explanation = (
                    f"Estimated cost (₹{cost:,.0f}) exceeds total available budget (₹{budget:,.0f}) "
                    f"by ₹{shortfall:,.0f}."
                )
            else:
                explanation = (
                    f"Feasible within budget. Estimated expenditure of ₹{cost:,.0f} represents "
                    f"{(cost / budget * 100):.1f}% of total budget. High suitability for {building.floors}-floor profile."
                )

            item = InterventionItem(
                id=item_id,
                name=meta["name"],
                category=meta["category"],
                description=meta["description"],
                cost_estimation_method=f"Deterministic rate: {meta['unit_cost_description']}",
                unit_cost_description=meta["unit_cost_description"],
                quantity=qty,
                quantity_unit=qty_unit,
                estimated_cost_inr=round(cost, 2),
                fits_budget=fits_budget,
                is_eligible=is_eligible,
                ineligibility_reason=ineligibility_reason,
                rank=None,
                score=score if fits_budget else None,
                explanation=explanation,
                limitations=meta["limitations"],
                evidence_status=meta["evidence_status"]
            )
            all_items.append(item)

            if is_eligible and fits_budget:
                feasible_candidates.append((score, item))

        # Rank feasible candidates by transparent score descending
        feasible_candidates.sort(key=lambda x: x[0], reverse=True)

        # Greedily build recommended set within total combined budget constraint
        ranked_recommended_items: List[InterventionItem] = []
        cumulative_cost = 0.0

        for idx, (sc, candidate) in enumerate(feasible_candidates, start=1):
            candidate_copy = candidate.model_copy()
            candidate_copy.rank = idx

            if (cumulative_cost + candidate_copy.estimated_cost_inr) <= budget:
                cumulative_cost += candidate_copy.estimated_cost_inr
                remaining_after = budget - cumulative_cost
                candidate_copy.explanation = (
                    f"Rank #{idx} recommendation (Score: {sc}/100). Selected into optimal package. "
                    f"Cost: ₹{candidate_copy.estimated_cost_inr:,.0f}. "
                    f"Remaining package budget balance: ₹{remaining_after:,.0f}."
                )
                ranked_recommended_items.append(candidate_copy)
            else:
                candidate_copy.explanation = (
                    f"Rank #{idx} (Score: {sc}/100). Individually affordable at ₹{candidate_copy.estimated_cost_inr:,.0f}, "
                    f"but excluded from the optimal package because combining it would exceed total budget constraint "
                    f"(Current combined: ₹{cumulative_cost:,.0f} + ₹{candidate_copy.estimated_cost_inr:,.0f} > ₹{budget:,.0f})."
                )
                # Keep in available items with updated explanation
                for item in all_items:
                    if item.id == candidate_copy.id:
                        item.rank = idx
                        item.explanation = candidate_copy.explanation

        # Ensure all items in all_items reflect their rank if ranked
        ranked_ids = {r.id: r for r in ranked_recommended_items}
        for item in all_items:
            if item.id in ranked_ids:
                item.rank = ranked_ids[item.id].rank
                item.explanation = ranked_ids[item.id].explanation

        remaining_budget = max(0.0, budget - cumulative_cost)

        assumptions = [
            "All cost figures are illustrative estimates based on standardized Indian benchmarks (CPWD / BEE / MNRE 2023-2024).",
            "Costs exclude applicable Goods and Services Tax (GST 18%), local transport, and site scaffolding.",
            "Rooftop solar sizing assumes 60% usable flat roof area after setbacks and access walkways at 10 m²/kWp.",
            "No unverified carbon or energy reductions are asserted without validated local energy consumption records."
        ]

        # Double benefit caveat if both roof interventions are eligible
        has_reflective = any(i.id == "reflective_roof" and i.fits_budget for i in all_items)
        has_insulation = any(i.id == "roof_insulation" and i.fits_budget for i in all_items)
        if has_reflective and has_insulation:
            assumptions.append(
                "Notice on Roof Interventions: Reflective roof and roof insulation both modify the rooftop envelope. "
                "Reflective coatings reject incident radiation at the exterior surface, while insulation resists heat conduction. "
                "Combining both is technically compatible but benefits interact and should be modeled together in detailed simulation."
            )

        return RecommendationResponse(
            budget_inr=budget,
            available_interventions=all_items,
            ranked_recommendations=ranked_recommended_items,
            total_recommended_cost_inr=round(cumulative_cost, 2),
            remaining_budget_inr=round(remaining_budget, 2),
            calculation_assumptions=assumptions,
            warnings=warnings,
            missing_information=missing_info
        )
