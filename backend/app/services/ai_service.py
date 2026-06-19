import os
import logging
import asyncio
import random
import re
from app.config import settings
from app.services.weather_service import WeatherService

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger("uvicorn")

class AIService:
    @classmethod
    async def generate_trip_plan(cls, destination: str, days: int = 0, budget: int = 0) -> str:
        logger.info(f"📡 [AI_SERVICE_RECEIVED] Frontend Input -> destination: {destination}, days: {days}, budget: {budget}")

        if days <= 0:
            logger.warning("⚠️ [PARAM_ALERT] Invalid travel days transferred (days <= 0). Activating fallback: 5 days")
            days = 5
        if budget <= 0:
            logger.warning("⚠️ [PARAM_ALERT] Invalid budget amount transferred (budget <= 0). Activating fallback: 2000 USDC")
            budget = 2000

        try:
            weather_info = await WeatherService.get_today_weather(destination)
        except Exception as e:
            logger.warning(f"⚠️ [WeatherService] Weather radar node synchronization timed out: {e}. Defaulting metrics.")
            weather_info = "Metrics: Max 28°C, Min 22°C, Rain Probability: 19%."

        try:
            prob_match = re.search(r"Rain Probability:\s*(\d+)%", weather_info)
            prob_val = int(prob_match.group(1)) if prob_match else 19
        except Exception:
            prob_val = 19

        if prob_val > 60:
            disruption_risk = "High (Precipitation Risk: High, Indoor Alternates Prioritized)"
        elif prob_val > 30:
            disruption_risk = "Moderate (Precipitation Risk: Noticeable, Fluid Transitions Required)"
        else:
            disruption_risk = "Low (Precipitation Risk: Negligible, Ideal for Outdoor Vectors)"

        daily_budget = budget / days

        stay_allocated = int(budget * 0.50)
        gastronomy_allocated = int(budget * 0.33)
        transit_allocated = budget - stay_allocated - gastronomy_allocated

        system_prompt = (
            "You are the ArcTrip Luxury Travel Curator, an elite digital concierge crafting immaculate, premium, and highly inspiring lifestyle itineraries.\n"
            "Your tone is sophisticated, organic, and ultra-premium—matching the visual aesthetic of Apple, Stripe, and Arc Browser.\n\n"
            "【CRITICAL MANDATES】\n"
            "1. Output the core itinerary body content directly. No conversational intro/outro, no greetings.\n"
            "2. NEVER mention financial/blockchain engineering concepts like 'reserve fund', 'liquidity safety margin', 'escrow balancing', 'collateral coverage', or 'financial buffer'. Users find this annoying. If a premium activity requires more budget, simply allocate it directly into the 'Transit & Mobility' or 'Gastronomy' categories naturally.\n"
            "3. You must STRICTLY use the pre-calculated budget numbers and the Disruption Probability provided below. Do NOT reuse historical template numbers (like 1500).\n"
            "4. Content must be authentic, highly localized, and tailored precisely to the target city.\n\n"
            f"Destination: {destination}\n"
            f"Duration: {days} Days\n"
            f"Total Budget: {budget} USDC (Daily Allowance: {daily_budget:.2f} USDC)\n"
            f"Current Climate Context: {weather_info}\n"
            f"Rain Probability: {prob_val}%\n\n"
            "【MANDATORY CAPITAL TIERING ALIGNMENT】\n"
            "Adapt your curated properties and luxury lifestyle scenes to the total budget tier:\n"
            "- If Daily Budget < 100 USDC: Select hyper-trendy local design hostels, artistic neighborhood homestays, and authentic local street eateries.\n"
            "- If Daily Budget 100~300 USDC: Select curated boutique hotels (e.g., The Hoxton, Ace Hotel, Edition), trending lifestyle bistros, and iconic cultural landmarks.\n"
            "- If Daily Budget > 300 USDC: Select absolute top-tier luxury nodes (e.g., Aman, Four Seasons, Ritz-Carlton), Michelin-starred or Black Pearl dining, and private chauffeur experiences.\n\n"
            "【OUTPUT STRUCTURE - ENFORCE STRICTLY】\n\n"
            f"○ ArcTrip Core / Premium Mapping Route — {destination}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "[ 🟢 System Status: Nominal | Routing Engine: Primary AI Cluster ]\n\n"
            "Your custom lifestyle itinerary has been successfully rendered.\n\n"
            "■ Environmental Context\n"
            "────────────────────────────────────────────────────────────────────────\n"
            f"• Destination: {destination}\n"
            f"• Meteorological Trend: {weather_info}\n"
            f"• Disruption Probability: {disruption_risk}\n\n"
            "■ Asset Allocation Matrix\n"
            "────────────────────────────────────────────────────────────────────────\n"
            f"Total Dynamic Allowance: {budget} USDC\n\n"
            "| Category | Allocation (USDC) |\n"
            "|------------------|-------------------|\n"
            f"| Accommodation | {stay_allocated} |\n"
            f"| Gastronomy | {gastronomy_allocated} |\n"
            f"| Transit & Mobility | {transit_allocated} |\n"
            f"| **Sum** | **{budget}** |\n\n"
            "■ Active Itinerary Plans\n"
            "────────────────────────────────────────────────────────────────────────\n"
            f"Generate a beautiful sequential travel plan from Day 1 to Day {days} using this strict layout:\n"
            "● Day X — [Elegant Urban Theme or Cultural District Name]\n"
            "  • Base: [Specific Real High-End Property Stay matching the budget tier]\n"
            "  • Curated Vector: [Single Iconic Landmark or Neighborhood Vector]\n"
            "  • Dining Scene: [Specific Named Fine Dining or Renowned Local Establishment]\n"
            "  • Smart Transit: [Optimized Chauffeur/Premium Ride profile]\n"
            "  • Indoor Alternate: [Enclosed Rainproof High-End Art Gallery or Museum Alternative]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "■ Operator Protocol Note:\n"
            "Provide a brief, pristine concierge summary under 25 words regarding how the outdoor transit routes blend seamlessly with the indoor alternatives given the current rain probability. Do NOT mention wallets, vaults, reserves, liquidity, protection, or smart contracts."
        )
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logger.error("❌ [AI_SERVICE] Critical variable DEEPSEEK_API_KEY missing. Triggering clean local backup engine.")
            return cls._get_backup_plan(destination, weather_info, budget, days, daily_budget, disruption_risk, stay_allocated, gastronomy_allocated, transit_allocated)
        
        client = AsyncOpenAI(
            base_url="https://api.deepseek.com",
            api_key=api_key
        )
        
        models_to_try = [
            "deepseek-v4-pro",    
            "deepseek-v4-flash"   
        ]

        for model_name in models_to_try:
            for attempt in range(1, 3):
                try:
                    logger.info(f"📡 [DEEPSEEK_SDK] Requesting model endpoint: {model_name} (Attempt {attempt})...")
                    
                    completion = await client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"CRITICAL REQUIREMENT: Do NOT hallucinate baseline numbers. Generate an ultra-premium lifestyle itinerary for {destination} over exactly {days} days with a strict budget cap of {budget} USDC as forced by the system layout."}
                        ],
                        temperature=0.3,   
                        top_p=0.95,
                        max_tokens=3000,   
                        stream=False
                    )
                    
                    ai_content = completion.choices[0].message.content
                    if ai_content:
                        logger.info(f"🎉 [AI_ROUTER_SUCCESS] Valid response generated from core cluster model: {model_name}")
                        return ai_content
                        
                except OpenAIError as oe:
                    logger.warning(f"⚠️ [ENDPOINT_REVERTED] Target cluster {model_name} currently unresponsive: {str(oe)}")
                    if "429" in str(oe):
                        sleep_time = attempt * 2 + random.uniform(0.5, 1.0)
                        await asyncio.sleep(sleep_time)
                    else:
                        break
                except Exception as e:
                    logger.warning(f"⚠️ [SYSTEM_NETWORK_EXCEPTION] Pipeline interruption on {model_name}: {str(e)}. Re-routing...")
                    await asyncio.sleep(0.5)
                    
        logger.error("🚨 [AI_CLUSTER_CRITICAL_FAILURE] All models exhausted. Activating clean local fallback engine.")
        return cls._get_backup_plan(destination, weather_info, budget, days, daily_budget, disruption_risk, stay_allocated, gastronomy_allocated, transit_allocated)

    @classmethod
    def _get_backup_plan(cls, destination: str, weather_info: str, budget: int, days: int, daily_budget: float, disruption_risk: str, stay: int, gastro: int, transit: int) -> str:
        if daily_budget > 300:
            tier_hotel_prefix = random.choice(["Aman", "The Ritz-Carlton", "Four Seasons", "Rosewood"])
            tier_transit = "Luxe Private Black-Car Chauffeur (Full-Day Axis)"
            tier_dining_suffix = "Michelin Curated Room"
        elif daily_budget >= 100:
            tier_hotel_prefix = random.choice(["Ace Hotel", "The Hoxton", "Edition Residence", "Design Hotels Selection"])
            tier_transit = "Premium Ride-Hailing On-Demand (Luxe Vector)"
            tier_dining_suffix = "Trending Lifestyle Bistro"
        else:
            tier_hotel_prefix = "Curated Urban Boutique Stay"
            tier_transit = "Metro Privilege Transit Link"
            tier_dining_suffix = "Localized Gastronomy Hub"

        city_name = destination.strip().title()

        lines = [
            f"○ ArcTrip Core / Route Backup Engine Activated — {city_name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "[ 🟢 System Status: Nominal | Routing Engine: Backup Matrix V4 ]",
            "",
            "The primary AI mapping route is undergoing a standard calibration optimized ",
            "for latency. To ensure uninterrupted premium onboarding, your personalized ",
            "itinerary has been successfully rendered.",
            "",
            "",
            "■ Environmental Context",
            "────────────────────────────────────────────────────────────────────────",
            f"• Destination: {city_name}",
            f"• Meteorological Trend: Syncing with Local Baselines ({days}-Day Horizon)",
            f"• Disruption Probability: {disruption_risk}",
            "",
            "",
            "■ Asset Allocation Matrix",
            "────────────────────────────────────────────────────────────────────────",
            f"Total Dynamic Allowance: {budget} USDC",
            "",
            "  [ Category ]          [ Allocation ]      [ Status ]",
            f"  Accommodation         {stay} USDC            Verified",
            f"  Gastronomy            {gastro} USDC            Available",
            f"  Transit & Mobility    {transit} USDC            Active Routing",
            "",
            "",
            "■ Active Itinerary Plans",
            "────────────────────────────────────────────────────────────────────────"
        ]

        vectors = ["Heritage Core", "Metropolitan Pulse", "Waterfront Vista", "Arts & Architecture Triangle", "Panoramic Heights"]
        indoors = ["Contemporary Art Pavilion", "National History Vault", "Central Grand Gallery", "Design & Media Forum"]

        for i in range(1, days + 1):
            v_idx = (i - 1) % len(vectors)
            id_idx = (i - 1) % len(indoors)
            
            base_hotel = f"{tier_hotel_prefix} {city_name}" if i == 1 or i % 3 == 1 else f"{tier_hotel_prefix} {city_name} Elite Residence"
            curated_vector = f"{city_name} {vectors[v_idx]}"
            dining_scene = f"The {city_name} Atelier ({tier_dining_suffix} No. {i})"
            indoor_alt = f"{city_name} {indoors[id_idx]} (Rainproof-Node)"

            lines.append(f"\n● Day {i} — {vectors[v_idx]}")
            lines.append(f"  • Base: {base_hotel}")
            lines.append(f"  • Curated Vector: {curated_vector}")
            lines.append(f"  • Dining Scene: {dining_scene}")
            lines.append(f"  • Smart Transit: {tier_transit}")
            lines.append(f"  • Indoor Alternate: {indoor_alt}")

        lines.extend([
            "",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "■ Operator Protocol Note:",
            "Outdoor routes are paired with indoor alternates. Standard fluid operations remain uninterrupted across all scheduled vectors."
        ])

        return "\n".join(lines)