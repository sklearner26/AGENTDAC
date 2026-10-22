"""
AgentDAC Proof-of-Concept (POC) Demo: TripMate AI Multi-Agent Pipeline.

Demonstrates end-to-end multi-agent observability using AgentDAC.
Simulates a real-world 5-agent travel concierge workflow (validator, flight,
hotel, itinerary, final budget synthesis) with tool invocations, LLM token/cost
tracking, specialized skills, and execution DAG reconstruction.

Run this script:
    uv run python examples/tripmate_poc_demo.py

View the reconstructed execution DAG in the dashboard:
    cd dashboard
    npm run dev
    # Open http://localhost:5173
"""

import time

from agentdac import AgentDAC


def main() -> None:
    print("=" * 70)
    print("  AgentDAC — TripMate AI Multi-Agent Observability POC")
    print("=" * 70)

    # 1. Initialize AgentDAC client (auto-starts local backend if needed)
    aog = AgentDAC(
        agent_id="tripmate-ai",
        fail_open=True,
    )
    print(f"[*] Client initialized for agent: {aog.config.agent_id}")
    print(f"[*] Connected backend: {aog.config.endpoint}")

    user_query = "Find flights from Delhi (DEL) to Tokyo (HND) next month, find a 4-star boutique hotel, and generate a 5-day itinerary."
    session_id = f"tripmate_demo_{int(time.time())}"

    print(f"\n[*] Starting session: {session_id}")
    print(f"[*] User Query: \"{user_query}\"")

    # 2. Wrap multi-agent workflow in a top-level session
    with aog.session(session_id=session_id, metadata={"user_query": user_query, "workflow": "autonomous_travel_planner"}):

        # -------------------------------------------------------------
        # STEP 1: Validator Agent (Verifies intent and route completeness)
        # -------------------------------------------------------------
        print("\n  [1/5] Executing: Validator Agent...")
        with aog.agent("validator_agent", attributes={"role": "Route & Intent Verification"}) as val_span:
            val_span.set_input({"query": user_query})
            with aog.llm(model="qwen-2.5-72b", provider="groq") as llm_span:
                time.sleep(0.05)  # simulate LLM latency
                llm_span.set_tokens(tokens_in=680, tokens_out=120)
                llm_span.set_cost(0.0006)
            val_span.set_output({
                "is_valid": True,
                "origin": "DEL",
                "destination": "HND",
                "intent": "leisure_vacation",
            })

        # -------------------------------------------------------------
        # STEP 2: Flight Finder Agent (Searches live airline routes)
        # -------------------------------------------------------------
        print("  [2/5] Executing: Flight Finder Agent...")
        with aog.agent("flight_agent", attributes={"role": "Airline & Route Discovery"}) as flight_span:
            flight_span.set_input({"origin": "DEL", "destination": "HND", "flexibility_days": 2})

            with aog.tool("route_resolver", input_data={"origin": "DEL", "destination": "HND"}) as tool_span:
                time.sleep(0.02)
                tool_span.set_output({"status": "resolved", "distance_km": 5840, "direct": True})

            with aog.tool("aviationstack_flight_search", input_data={"dep": "DEL", "arr": "HND"}) as tool_span:
                time.sleep(0.06)
                tool_span.set_output({
                    "flights_found": 3,
                    "best_option": {"carrier": "All Nippon Airways (NH838)", "price_usd": 680, "duration": "8h 15m"},
                })

            with aog.llm(model="qwen-2.5-72b", provider="groq") as llm_span:
                time.sleep(0.04)
                llm_span.set_tokens(tokens_in=420, tokens_out=110)
                llm_span.set_cost(0.0004)

            flight_span.set_output({
                "selected_flight": "ANA NH838 (DEL -> HND)",
                "fare_usd": 680,
            })

        # -------------------------------------------------------------
        # STEP 3: Hotel Scout Agent (Evaluates accommodations & amenities)
        # -------------------------------------------------------------
        print("  [3/5] Executing: Hotel Scout Agent...")
        with aog.agent("hotel_agent", attributes={"role": "Accommodation Search & Quality Ranking"}) as hotel_span:
            hotel_span.set_input({"destination": "Tokyo", "tier": "4-star", "nights": 5})

            with aog.skill("luxury_budget_scoring", attributes={"algorithm": "weighted_amenities"}) as skill_span:
                skill_span.set_input({"max_price_per_night": 220, "preferred_district": "Shinjuku"})
                skill_span.set_output({"selected_tier": "4-star", "confidence": 0.96})

            with aog.tool("tavily_web_search", input_data={"query": "top boutique 4-star hotels Shinjuku Tokyo"}) as tool_span:
                time.sleep(0.05)
                tool_span.set_output({
                    "results": ["Hotel Gracery Shinjuku", "Keio Plaza Hotel Tokyo", "THE KNOT TOKYO Shinjuku"],
                })

            with aog.llm(model="qwen-2.5-72b", provider="groq") as llm_span:
                time.sleep(0.04)
                llm_span.set_tokens(tokens_in=560, tokens_out=140)
                llm_span.set_cost(0.0005)

            hotel_span.set_output({
                "selected_hotel": "THE KNOT TOKYO Shinjuku",
                "price_per_night_usd": 185,
                "total_hotel_cost_usd": 925,
            })

        # -------------------------------------------------------------
        # STEP 4: Itinerary Agent (Builds day-by-day schedule)
        # -------------------------------------------------------------
        print("  [4/5] Executing: Itinerary Agent...")
        with aog.agent("itinerary_agent", attributes={"role": "Day-by-Day Schedule Builder"}) as itin_span:
            itin_span.set_input({"days": 5, "city": "Tokyo", "interests": ["culture", "food", "tech"]})

            with aog.skill("itinerary_pacing_balancer", attributes={"pace": "moderate"}) as skill_span:
                skill_span.set_input({"max_activities_per_day": 3})
                skill_span.set_output({"scheduled_pace": "optimal", "rest_stops": 5})

            with aog.llm(model="qwen-2.5-72b", provider="groq") as llm_span:
                time.sleep(0.06)
                llm_span.set_tokens(tokens_in=1240, tokens_out=480)
                llm_span.set_cost(0.0016)

            itin_span.set_output({
                "days_planned": 5,
                "highlights": ["Shibuya Sky", "Meiji Shrine", "Akihabara Tech Crawl", "Tsukiji Outer Market"],
            })

        # -------------------------------------------------------------
        # STEP 5: Final Synthesis Agent (Aggregates budget & creates summary)
        # -------------------------------------------------------------
        print("  [5/5] Executing: Final Synthesis Agent...")
        with aog.agent("final_agent", attributes={"role": "Budget Synthesis & Final Presentation"}) as final_span:
            with aog.tool("currency_converter", input_data={"amount_jpy": 240000, "target": "USD"}) as tool_span:
                time.sleep(0.01)
                tool_span.set_output({"converted_usd": 1605.00, "rate": 0.0067})

            with aog.llm(model="qwen-2.5-72b", provider="groq") as llm_span:
                time.sleep(0.03)
                llm_span.set_tokens(tokens_in=450, tokens_out=220)
                llm_span.set_cost(0.0006)

            final_span.set_output({
                "status": "completed",
                "total_estimated_cost_usd": 1605.00,
                "summary": "5-Day Tokyo Exploration: ANA Flight ($680) + THE KNOT Hotel ($925)",
            })

    # Flush all events asynchronously to ensure backend has persisted them
    aog.flush(timeout=3.0)

    print("\n" + "=" * 70)
    print("  [SUCCESS] All 5 agent spans, tools, skills, and LLM telemetry exported!")
    print(f"  Session ID: {session_id}")
    print("=" * 70)
    print("\nTo inspect the interactive execution DAG, timeline waterfall, and AI Chat:")
    print("  1. Ensure the React dashboard is running:")
    print("     cd dashboard && npm run dev")
    print("  2. Open http://localhost:5173")
    print(f"  3. Select session '{session_id}' from the session list.")
    print("=" * 70)

if __name__ == "__main__":
    main()
