import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.extend([r"c:\Users\premk\Videos\gen-transform-ai\Backend", r"c:\Users\premk\Videos\gen-transform-ai"])

from Backend.app.services.presentation.pptx_generator import create_pptx_presentation

output_dir = Path(r"c:\Users\premk\Videos\gen-transform-ai\outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# Define full presentation data for DraXon Geo-Tagged Waste Reporting & Tracking
presentation_data = {
    "presentation_title": "Geo-Tagged Waste Reporting and Tracking",
    "subtitle": "AI-Driven Urban Sanitation & Verification Platform • Team DraXon",
    "theme": "spotify_emerald",
    "slides": [
        {
            "slide_number": 1,
            "title": "Geo-Tagged Waste Reporting & Tracking",
            "layout": "title",
            "subtitle": "Closing the Urban Sanitation Loop with Vision AI & Geo-Spatial Intelligence\nTeam DraXon | Theme: Geo-Tech",
            "content": [],
            "speaker_notes": "Welcome everyone. Today we present Team DraXon's AI-powered Geo-Tagged Waste Reporting and Tracking system, designed to transform municipal waste management through computer vision, automated priority dispatch, and verified cleanups.",
            "visual_recommendation": "High-contrast dark emerald hero title slide with Geo-Tech branding"
        },
        {
            "slide_number": 2,
            "title": "The Urban Waste Crisis: Real-World Ground Truth",
            "layout": "bullet_points",
            "content": [
                "Delhi generates >11,000 tons of solid waste daily, leading to overwhelmed landfills and stakeholder bottlenecks.",
                "Tamil Nadu generates 14,200 - 15,200 tonnes/day: while 66% is processed, ~34% (~5,000 tonnes/day) remains unmanaged.",
                "Manual reporting systems rely on vague text complaints with zero visual proof and no urgency classification.",
                "Delayed response times cause severe public health hazards, toxic drain blockages, and environmental degradation."
            ],
            "speaker_notes": "Let's examine the staggering data. In Tamil Nadu alone, 5,000 tonnes of municipal waste ends up dumped in open drains, roadsides, and unmanaged sites every single day because current reporting mechanisms lack speed, proof, and accountability.",
            "visual_recommendation": "Split statistics card highlighting 11,000 T/day Delhi vs 15,200 T/day Tamil Nadu with 34% unmanaged gap"
        },
        {
            "slide_number": 3,
            "title": "Our Solution: Closed-Loop AI & Geo-Tracking",
            "layout": "bullet_points",
            "content": [
                "Citizen Photo Upload: Instant camera capture with automatic GPS geo-tagging prevents fake reports.",
                "Automated AI Dual-Verification: MobileNetV2 screens waste vs non-waste; YOLOv8 classifies waste typology.",
                "Dynamic Priority Escalation: Heatmap clustering automatically elevates priority for recurrent reports.",
                "Task Dispatch & Route Routing: Municipal cleaners receive geotargeted pickup tasks directly on mobile.",
                "Before/After Verification: Siamese Neural Network validates cleanliness before granting incentive rewards."
            ],
            "speaker_notes": "Our system closes the loop from citizen reporting to verified cleanup. Citizens upload photos which are instantly classified by vision AI and mapped to real-time heatmaps for rapid municipal deployment.",
            "visual_recommendation": "Step-by-step 5-stage closed loop workflow diagram"
        },
        {
            "slide_number": 4,
            "title": "Technical Architecture & Deep Learning Stack",
            "layout": "two_column",
            "column_left": [
                "Client & Backend Infrastructure:",
                "• Frontend: React Native (Cross-Platform Mobile)",
                "• Backend Engine: Node.js High-Throughput REST API",
                "• Database: MongoDB Geospatial Document Store",
                "• Geo-Services: Google Maps API & Spatial Indexing"
            ],
            "column_right": [
                "AI / Computer Vision Pipeline:",
                "• Waste Detection: MobileNetV2 (Edge-optimized)",
                "• Waste Classification: YOLOv8 Object Detection",
                "• Cleanup Verification: Siamese Neural Network",
                "• Ingestion Speed: Sub-second AI inference"
            ],
            "speaker_notes": "Our tech stack combines mobile-first React Native with high-performance computer vision. MobileNetV2 handles initial validation on low latency, YOLOv8 identifies hazardous materials, and Siamese Networks compare pre- and post-cleanup photos.",
            "visual_recommendation": "Two-column architectural blueprint comparing application tier vs AI model inference tier"
        },
        {
            "slide_number": 5,
            "title": "Competitive Advantage vs Existing Systems",
            "layout": "two_column",
            "column_left": [
                "Traditional Systems (e.g., Swachhata App):",
                "• Manual text complaint logging",
                "• Zero automated AI image validation",
                "• No dynamic priority escalation for hazards",
                "• Lack of proof for post-cleaning completion",
                "• Low citizen engagement and high drop-off"
            ],
            "column_right": [
                "DraXon AI-Driven Platform:",
                "• Instant photo capture with verified GPS stamps",
                "• Automated vision classification (YOLOv8)",
                "• Hotspot aggregation & priority scoring",
                "• Siamese Neural Network before/after audit",
                "• Gamified redeemable cash-credit incentive loop"
            ],
            "speaker_notes": "Compared to legacy apps like the Swachhata App, DraXon provides end-to-end auditability. Cleaners cannot submit false completion reports because Siamese neural networks mathematically verify cleanliness before credits are issued.",
            "visual_recommendation": "Side-by-side comparison matrix with green checkmarks and red flags"
        },
        {
            "slide_number": 6,
            "title": "Economic Viability & Gamified Incentives",
            "layout": "bullet_points",
            "content": [
                "Citizen Credit Rewards: Active citizens earn redeemable points for validated waste submissions.",
                "Performance-Based Sanitation Wages: Cleaning staff receive automated bonus credits upon verified job completion.",
                "Redemption Mechanism: Points convert into municipal tax credits, utility rebates, or direct cash incentives.",
                "Operational Cost Savings: 40%+ reduction in redundant municipal inspection rounds and false callouts."
            ],
            "speaker_notes": "We solved the adoption problem through economic alignment. Citizens are incentivized to report, and sanitation workers receive bonuses upon verified cleanup, creating a self-sustaining civic ecosystem.",
            "visual_recommendation": "Incentive flywheel graphic illustrating citizen report -> AI audit -> cleaner dispatch -> cash reward"
        },
        {
            "slide_number": 7,
            "title": "Implementation Roadmap & Impact Metrics",
            "layout": "bullet_points",
            "content": [
                "Phase 1: Pilot deployment in high-density municipal wards across Tamil Nadu and Delhi.",
                "Phase 2: Integration with municipal GIS command centers and automated truck routing.",
                "Phase 3: Nationwide expansion with multi-lingual voice prompts and offline geo-caching.",
                "Target KPI: 75% reduction in complaint-to-cleanup turnaround time and 90%+ citizen satisfaction."
            ],
            "speaker_notes": "Our phased deployment begins in priority urban hotspots, transitioning municipal sanitation from reactive complaints to predictive, AI-driven dispatch.",
            "visual_recommendation": "3-stage horizontal milestone timeline with key performance indicator badges"
        },
        {
            "slide_number": 8,
            "title": "Join Us in Revolutionizing Urban Sanitation",
            "layout": "title",
            "subtitle": "Team DraXon • Empowering Citizens, Equipping Workers, Cleansing Cities\nContact: project-d倍xon@doclink.ai | GitHub: /gen-transform-ai",
            "content": [],
            "speaker_notes": "Thank you for your time. We are ready to answer your questions and demonstrate the live platform.",
            "visual_recommendation": "Bold call-to-action summary slide with emerald accents and contact information"
        }
    ]
}

pptx_stream = create_pptx_presentation(presentation_data, theme_name="spotify_emerald")
pptx_file_path = output_dir / "salem_waste_management_presentation.pptx"
with open(pptx_file_path, "wb") as f:
    f.write(pptx_stream.getvalue())

print(f"[OK] Presentation successfully generated and saved to: {pptx_file_path}")
print(f"File size: {os.path.getsize(pptx_file_path)} bytes")
