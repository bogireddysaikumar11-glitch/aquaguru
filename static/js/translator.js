/**
 * AquaGuru Universal Real-Time Client & Server Translator
 * Instantly converts all text, inputs, buttons, tables, charts, modals,
 * and dynamic components between English and Telugu across all site features.
 */

(function () {
    'use strict';

    // Complete Bidirectional Translation Dictionary
    const dictionary = {
        // Navigation & Menus
        "Main Menu": "ప్రధాన మెనూ",
        "Dashboard": "డాష్‌బోర్డ్",
        "Ponds": "చెరువులు",
        "Feed Calculator": "ఫీడ్ కాలిక్యులేటర్",
        "Water Quality": "నీటి నాణ్యత",
        "Growth": "పెరుగుదల",
        "Expenses": "ఖర్చులు",
        "Inventory": "ఇన్వెంటరీ",
        "Harvest": "పంట కోత",
        "Notifications": "నోటిఫికేషన్లు",
        "AI Assistant": "AI సహాయకుడు",
        "AI Farm Assistant": "AI ఫార్మ్ సహాయకుడు",
        "AI Farming Assistant": "AI ఫార్మ్ సహాయకుడు",
        "Reports": "నివేదికలు",
        "Reports Center": "నివేదికల కేంద్రం",
        "Profile": "ప్రొఫైల్",
        "User Profile": "యూజర్ ప్రొఫైల్",
        "My Profile": "నా ప్రొఫైల్",
        "Logout": "లాగ్ అవుట్",
        "Home": "హోమ్",
        "Alerts": "హెచ్చరికలు",
        "Firebase Cloud": "ఫైర్‌బేస్ క్లౌడ్",

        // Actions & Controls
        "Actions": "చర్యలు",
        "Save": "సేవ్ చేయండి",
        "Cancel": "రద్దు చేయండి",
        "Delete": "తొలగించు",
        "Edit": "సవరించు",
        "Refresh": "రిఫ్రెష్",
        "Date": "తేదీ",
        "Status": "స్థితి",
        "Notes": "గమనికలు",
        "Loading...": "లోడ్ అవుతోంది...",
        "Welcome back": "తిరిగి స్వాగతం",
        "Good": "మంచిది",
        "Moderate": "మధ్యస్థం",
        "Poor": "బలహీనమైనది",
        "No Data": "డేటా లేదు",
        "Active": "క్రియాశీలకం",
        "Harvested": "కోత పూర్తయింది",
        "Preparing": "సిద్ధమవుతోంది",
        "Days": "రోజులు",
        "Today": "నేడు",
        "Online": "ఆన్‌లైన్",
        "Offline": "ఆఫ్‌లైన్",
        "View All": "అన్నీ చూడండి",
        "Submit": "సమర్పించు",
        "Back": "వెనుకకు",
        "Close": "మూసివేయి",
        "Calculate": "లెక్కించు",
        "Export": "ఎగుమతి",
        "Print": "ప్రింట్",
        "Send": "పంపండి",

        // Dashboard
        "Total Ponds": "మొత్తం చెరువులు",
        "Total Feed Used": "మొత్తం ఫీడ్ వాడకం",
        "Current DOC": "ప్రస్తుత DOC",
        "Avg ABW": "సగటు ABW",
        "Water Quality Status": "నీటి నాణ్యత స్థితి",
        "Survival": "మనుగడ శాతం",
        "Quick Actions": "శీఘ్ర చర్యలు",
        "Add Feed Record": "ఫీడ్ రికార్డ్ జోడించండి",
        "Log Water Quality": "నీటి నాణ్యతను నమోదు చేయండి",
        "Record Growth": "పెరుగుదలను రికార్డ్ చేయండి",
        "Add Expense": "ఖర్చును జోడించండి",
        "Recent Activity": "ఇటీవలి కార్యాచరణ",
        "Last 5 Growth Records": "గత 5 పెరుగుదల రికార్డులు",
        "Financial Summary": "ఆర్థిక సారాంశం",
        "Total Feed Cost": "మొత్తం ఫీడ్ ఖర్చు",
        "Total Expenses": "మొత్తం ఖర్చులు",
        "Feed": "ఫీడ్",
        "Water": "నీరు",
        "Expense": "ఖర్చు",
        "No growth data recorded yet. Start logging to see analytics!": "ఇంకా పెరుగుదల డేటా రికార్డ్ కాలేదు. విశ్లేషణలు చూడటానికి లాగింగ్ ప్రారంభించండి!",
        "No data recorded yet.": "ఇంకా డేటా రికార్డ్ కాలేదు.",
        "Smart Shrimp & Aquaculture Farm Management": "స్మార్ట్ రొయ్యల & ఆక్వాసాగు నిర్వహణ వ్యవస్థ",

        // Ponds
        "Pond Management": "చెరువుల నిర్వహణ",
        "Pond Name": "చెరువు పేరు",
        "Area (m²)": "విస్తీర్ణం (చ.మీ)",
        "Area": "విస్తీర్ణం",
        "Species": "రకం / జాతులు",
        "Seed Count": "విత్తనాల సంఖ్య",
        "Stocking Date": "నిల్వ చేసిన తేదీ",
        "Days in Culture": "సంస్కృతి రోజులు (DOC)",
        "Add New Pond": "కొత్త చెరువును జోడించండి",
        "Save Pond": "చెరువును సేవ్ చేయండి",
        "Edit Pond": "చెరువును సవరించండి",
        "Save Changes": "మార్పులను సేవ్ చేయండి",
        "Delete Pond": "చెరువును తొలగించండి",
        "Select Pond": "చెరువును ఎంచుకోండి",
        "Pond Details": "చెరువు వివరాలు",
        "Are you sure you want to delete this pond?": "మీరు ఖచ్చితంగా ఈ చెరువును తొలగించాలనుకుంటున్నారా?",

        // Feed Calculator
        "Feed Calculator & Records": "ఫీడ్ కాలిక్యులేటర్ & రికార్డులు",
        "DOC (Days of Culture)": "DOC (సంస్కృతి రోజులు)",
        "DOC": "DOC",
        "ABW (g)": "సగటు బరువు ABW (గ్రా)",
        "ABW": "ABW",
        "Survival (%)": "మనుగడ శాతం (%)",
        "Feed %": "ఫీడ్ శాతం %",
        "Biomass (kg)": "జీవ ద్రవ్యరాశి (కిలోలు)",
        "Daily Feed (kg)": "రోజువారీ ఫీడ్ (కిలోలు)",
        "Feed Per Session (kg)": "పూటకు ఫీడ్ (కిలోలు)",
        "Save Feed Record": "ఫీడ్ రికార్డును సేవ్ చేయండి",
        "Save Record": "రికార్డును సేవ్ చేయండి",
        "Feed Type": "ఫీడ్ రకం",
        "Amount": "మొత్తం పరిమాణం",
        "Total Amount (kg)": "మొత్తం పరిమాణం (కిలోలు)",
        "Feed History": "ఫీడ్ చరిత్ర",
        "Sessions Per Day": "రోజుకు పూటల సంఖ్య",
        "Pellet": "గుళికలు (Pellet)",
        "Pellets": "గుళికలు (Pellets)",
        "Starter": "స్టార్టర్ (Starter)",
        "Grower": "గ్రోవర్ (Grower)",
        "Finisher": "ఫినిషర్ (Finisher)",
        "Crumbles": "క్రంబుల్స్ (Crumbles)",
        "Powder": "పౌడర్ (Powder)",
        "Please fill in all fields": "దయచేసి అన్ని వివరాలను నమోదు చేయండి",
        "Error calculating feed. Please try again.": "ఫీడ్ లెక్కించడంలో లోపం. దయచేసి మళ్లీ ప్రయత్నించండి.",

        // Water Quality
        "Water Quality Monitoring": "నీటి నాణ్యత పర్యవేక్షణ",
        "Log Water Parameters": "నీటి పారామితులను నమోదు చేయండి",
        "pH Level": "pH స్థాయి",
        "pH": "pH",
        "Dissolved Oxygen (DO mg/L)": "కరగిన ఆక్సిజన్ (DO mg/L)",
        "DO (mg/L)": "DO (mg/L)",
        "DO": "DO",
        "Temperature (°C)": "ఉష్ణోగ్రత (°C)",
        "Temperature": "ఉష్ణోగ్రత",
        "Salinity (ppt)": "ఉప్పు శాతం (Salinity ppt)",
        "Salinity": "ఉప్పు శాతం",
        "Ammonia (ppm)": "అమ్మోనియా (Ammonia ppm)",
        "Ammonia": "అమ్మోనియా",
        "Nitrite (ppm)": "నైట్రైట్ (Nitrite ppm)",
        "Nitrite": "నైట్రైట్",
        "Alkalinity (ppm)": "ఆల్కలీనిటీ (Alkalinity ppm)",
        "Alkalinity": "ఆల్కలీనిటీ",
        "Transparency (cm)": "పారదర్శకత (Transparency cm)",
        "Transparency": "పారదర్శకత",
        "Save Log": "లాగ్‌ను సేవ్ చేయండి",
        "Save Water Log": "వాటర్ లాగ్‌ను సేవ్ చేయండి",
        "Water Quality Log History": "నీటి నాణ్యత లాగ్ చరిత్ర",
        "Water Log History": "నీటి లాగ్ చరిత్ర",
        "Optimal Ranges Guidelines": "సరైన పరిమాణాల మార్గదర్శకాలు",
        "Water Photo / Sample": "నీటి ఫోటో / శాంపిల్",
        "Water Photo": "నీటి ఫోటో",
        "Choose File": "ఫైల్ ఎంచుకోండి",
        "Take Photo": "ఫోటో తీయండి",
        "Choose from Files": "ఫైల్స్ నుండి ఎంచుకోండి",
        "Take Photo (Camera)": "కెమెరాతో ఫోటో తీయండి",
        "Open Live Camera": "లైవ్ కెమెరా తెరవండి",
        "Capture Photo": "ఫోటో క్యాప్చర్ చేయండి",
        "Remove Photo": "ఫోటోను తొలగించండి",
        "Photo Preview": "ఫోటో ముందస్తు వీక్షణ",
        "Water Sample Photo": "నీటి శాంపిల్ ఫోటో",
        "View Photo": "ఫోటో చూడండి",
        "No Photo": "ఫోటో లేదు",
        "Live Camera Capture": "లైవ్ కెమెరా క్యాప్చర్",
        "Take Snapshot": "స్నాప్‌షాట్ తీయండి",
        "Please allow camera permissions to take a photo.": "ఫోటో తీయడానికి దయచేసి కెమెరా అనుమతులను ఇవ్వండి.",
        "Pond Water Sample Photo": "చెరువు నీటి శాంపిల్ ఫోటో",

        // Growth
        "Growth & Sampling": "పెరుగుదల & శాంప్లింగ్",
        "Growth History & Analytics": "పెరుగుదల చరిత్ర & విశ్లేషణలు",
        "Record Sampling Data": "శాంప్లింగ్ డేటాను రికార్డ్ చేయండి",
        "ADG (g/day)": "రోజువారీ సగటు పెరుగుదల (ADG)",
        "ADG": "ADG",
        "FCR": "FCR (ఫీడ్ కన్వర్షన్)",
        "Length (cm)": "పొడవు (సెం.మీ)",
        "Average Body Weight": "సగటు శరీర బరువు",
        "Growth Curve": "పెరుగుదల గ్రాఫ్",
        "Sampling History": "శాంప్లింగ్ చరిత్ర",

        // Expenses
        "Expense Tracking": "ఖర్చుల ట్రాకింగ్",
        "Log New Expense": "కొత్త ఖర్చును నమోదు చేయండి",
        "Category": "విభాగం",
        "Amount ($)": "మొత్తం ($)",
        "Amount (₹)": "మొత్తం (₹)",
        "Description": "వివరణ",
        "Save Expense": "ఖర్చును సేవ్ చేయండి",
        "Total Spent": "మొత్తం ఖర్చు",
        "This Month": "ఈ నెల",
        "Expense History": "ఖర్చుల చరిత్ర",
        "Electricity": "కరెంట్ బిల్లు",
        "Labor": "కూలీలు / శ్రామికులు",
        "Fuel": "డీజిల్ / ఇంధనం",
        "Maintenance": "నిర్వహణ ఖర్చులు",
        "Chemicals / Medicine": "మందులు & రసాయనాలు",
        "Seed / Post Larvae": "విత్తనాలు (PL సీడ్)",
        "Other": "ఇతర ఖర్చులు",

        // Inventory
        "Inventory Management": "స్టాక్ & ఇన్వెంటరీ నిర్వహణ",
        "Add Inventory Item": "కొత్త వస్తువును జోడించండి",
        "Item Name": "వస్తువు పేరు",
        "Unit": "యూనిట్ / కొలత",
        "Quantity": "పరిమాణం",
        "Min Quantity": "కనిష్ట పరిమాణం",
        "Current Quantity": "ప్రస్తుత నిల్వ",
        "Price per Unit ($)": "యూనిట్ ధర ($)",
        "Price per Unit (₹)": "యూనిట్ ధర (₹)",
        "Supplier": "సరఫరాదారు",
        "Expiry Date": "గడువు తేదీ",
        "Low Stock Alert!": "తక్కువ స్టాక్ హెచ్చరిక!",
        "In Stock": "నిల్వ ఉంది",
        "Low Stock": "తక్కువ నిల్వ",
        "Out of Stock": "స్టాక్ అయిపోయింది",
        "Inventory Items": "స్టాక్ వస్తువుల జాబితా",
        "Save Item": "వస్తువును సేవ్ చేయండి",

        // Harvest
        "Harvest & Profit": "పంట కోత & లాభాల వివరాలు",
        "Record Pond Harvest": "కోత వివరాలను నమోదు చేయండి",
        "Harvest Date": "కోత తేదీ",
        "Production (kg)": "మొత్తం దిగుబడి (కిలోలు)",
        "Average Weight (g)": "సగటు బరువు (గ్రా)",
        "Price per kg ($)": "కిలో ధర ($)",
        "Price per kg (₹)": "కిలో ధర (₹)",
        "Total Cost ($)": "మొత్తం ఖర్చు ($)",
        "Total Cost (₹)": "మొత్తం ఖర్చు (₹)",
        "Income ($)": "మొత్తం ఆదాయం ($)",
        "Income (₹)": "మొత్తం ఆదాయం (₹)",
        "Profit ($)": "నికర లాభం ($)",
        "Profit (₹)": "నికర లాభం (₹)",
        "Save Harvest": "కోతను సేవ్ చేయండి",
        "Harvest History": "గత పంటల చరిత్ర",
        "Total Income": "మొత్తం ఆదాయం",
        "Total Profit": "మొత్తం నికర లాభం",
        "Net Profit": "నికర లాభం",
        "Survival Rate (%)": "మనుగడ శాతం (%)",

        // Shrimp Market Rates
        "Market Rates": "మార్కెట్ ధరలు",
        "Daily Shrimp Market Rates": "రోజువారీ రొయ్యల మార్కెట్ ధరలు",
        "Live Shrimp Market Rates": "ప్రత్యక్ష రొయ్యల మార్కెట్ ధరలు",
        "Live Market Rates": "ప్రత్యక్ష మార్కెట్ ధరలు",
        "Market Rates & Price Trends": "మార్కెట్ ధరలు & ధరల సరళి",
        "Count": "కౌంట్ (Count)",
        "Count Size": "కౌంట్ పరిమాణం",
        "Price per KG": "కిలో ధర",
        "Market Hub": "మార్కెట్ కేంద్రం",
        "Select Location": "కేంద్రాన్ని ఎంచుకోండి",
        "All Hubs": "అన్ని కేంద్రాలు",
        "Price Trend": "ధరల సరళి",
        "Price Trend (7-30 Days)": "ధరల సరళి (7-30 రోజులు)",
        "Market Value Calculator": "మార్కెట్ విలువ కాలిక్యులేటర్",
        "Calculate Revenue": "ఆదాయాన్ని లెక్కించండి",
        "Expected Harvest (kg)": "అంచనా పంట దిగుబడి (కిలోలు)",
        "Estimated Value": "అంచనా మార్కెట్ విలువ",
        "Estimated Earnings": "అంచనా ఆదాయం",
        "Log New Market Rate": "కొత్త మార్కెట్ ధరను నమోదు చేయండి",
        "Save Rate": "ధరను సేవ్ చేయండి",
        "Price Change": "ధర మార్పు",
        "Price Change (vs Yesterday)": "ధర మార్పు (నిన్నటితో పోలిస్తే)",
        "Species": "రకం",
        "Vannamei": "వనామి (Vannamei)",
        "Black Tiger": "బ్లాక్ టైగర్ (Black Tiger)",
        "Bhimavaram": "భీమవరం (Bhimavaram)",
        "Nellore": "నెల్లూరు (Nellore)",
        "Kakinada": "కాకినాడ (Kakinada)",
        "Surat": "సూరత్ (Surat)",
        "Amalapuram": "అమలాపురం (Amalapuram)",
        "Latest Rates Date": "తాజా ధరల తేదీ",
        "View All Market Rates": "అన్ని మార్కెట్ ధరలను చూడండి",
        "Check Market Rates": "మార్కెట్ ధరలను తనిఖీ చేయండి",
        "Today's Rate": "నేటి ధర",
        "Andhra Pradesh": "ఆంధ్రప్రదేశ్ (Andhra Pradesh)",
        "20 Count": "20 కౌంట్",
        "25 Count": "25 కౌంట్",
        "30 Count": "30 కౌంట్",
        "40 Count": "40 కౌంట్",
        "45 Count": "45 కౌంట్",
        "50 Count": "50 కౌంట్",
        "60 Count": "60 కౌంట్",
        "70 Count": "70 కౌంట్",
        "80 Count": "80 కౌంట్",
        "90 Count": "90 కౌంట్",
        "100 Count": "100 కౌంట్",
        "20c": "20 కౌంట్",
        "25c": "25 కౌంట్",
        "30c": "30 కౌంట్",
        "40c": "40 కౌంట్",
        "45c": "45 కౌంట్",
        "50c": "50 కౌంట్",
        "60c": "60 కౌంట్",
        "70c": "70c",
        "80c": "80c",
        "90c": "90c",
        "100c": "100c",
        "Shrimp": "రొయ్యలు",
        "Fish": "చేపలు",
        "Today's Count Prices": "నేటి కౌంట్ ధరలు",
        "Count Prices": "కౌంట్ ధరలు",
        "Market Price": "మార్కెట్ ధర",
        "Rohu": "రోహు (Rohu)",
        "Catla": "బొచ్చె (Catla)",
        "Tilapia": "తిలాపియా (Tilapia)",
        "Pangasius": "పంగసియస్ (Pangasius)",
        "Sea Bass": "పండుగప్ప (Sea Bass)",
        "Murrel": "కొర్రమీను (Murrel)",
        "Category": "వర్గం",
        "Help Desk": "సహాయ కేంద్రం",
        "Only administrators can update market rates!": "మార్కెట్ ధరలను నిర్వాహకులు (Admin) మాత్రమే మార్చగలరు!",
        "Only administrators can perform this action.": "ఈ చర్యను అడ్మిన్ మాత్రమే చేయగలరు.",
        "Admin Verified Live Rates": "అడ్మిన్ ధృవీకరించిన ప్రత్యక్ష ధరలు",
        "Admin Only": "అడ్మిన్ మాత్రమే",
        "Delete Rate": "ధరను తొలగించండి",
        "Are you sure you want to delete this rate?": "మీరు ఖచ్చితంగా ఈ ధర రికార్డును తొలగించాలనుకుంటున్నారా?",

        // Notifications
        "Notifications & Reminders": "నోటిఫికేషన్లు & రిమైండర్లు",
        "Mark All as Read": "అన్నీ చదివినట్లు గుర్తించండి",
        "No Notifications": "నోటిఫికేషన్లు లేవు",
        "You're all caught up!": "అన్ని అలర్టులు క్లియర్ చేయబడ్డాయి!",
        "New": "కొత్తది",
        "Reminder": "రిమైండర్",
        "Alert": "హెచ్చరిక",

        // AI Assistant
        "Ask AI Assistant": "AI ని ప్రశ్న అడగండి",
        "Type your aquaculture question...": "మీ ఆక్వాసాగు సందేహాన్ని ఇక్కడ టైప్ చేయండి...",
        "Ask me anything about shrimp farming, water quality, diseases, or feed management!": "రొయ్యల సాగు, నీటి నాణ్యత, వ్యాధుల నివారణ లేదా ఫీడ్ నిర్వహణ గురించి ఏదైనా అడగండి!",
        "Low DO": "తక్కువ DO సమస్య",
        "High Ammonia": "అధిక అమ్మోనియా",
        "White Gut": "వైట్ గట్ వ్యాధి",
        "Water Quality Guidelines": "నీటి నాణ్యత మార్గదర్శకాలు",
        "Quick Suggestions": "శీఘ్ర ప్రశ్నలు",

        // Reports
        "Feed Report": "ఫీడ్ నివేదిక",
        "Growth Report": "పెరుగుదల నివేదిక",
        "Expense Report": "ఖర్చుల నివేదిక",
        "Water Report": "నీటి నాణ్యత నివేదిక",
        "Water Quality Report": "నీటి నాణ్యత నివేదిక",
        "Harvest Report": "పంట దిగుబడి నివేదిక",
        "Complete Farm Report": "సంపూర్ణ ఫార్మ్ నివేదిక",
        "Generate Report": "నివేదికను రూపొందించండి",
        "View feed consumption and usage statistics": "ఫీడ్ వినియోగం మరియు వాడకం గణాంకాలను చూడండి",
        "Track shrimp growth and performance metrics": "రొయ్యల పెరుగుదల మరియు పనితీరును ట్రాక్ చేయండి",
        "Analyze farm expenses by category": "విభాగాల వారీగా ఫార్మ్ ఖర్చులను విశ్లేషించండి",
        "Check historical water quality trends": "గత నీటి నాణ్యత మార్పులను పరిశీలించండి",
        "Review harvest yields and profitability": "పంట దిగుబడి మరియు లాభదాయకతను సమీక్షించండి",
        "Comprehensive report covering all farm metrics": "అన్ని వివరాలతో కూడిన సమగ్ర నివేదిక",
        "Report Preview": "నివేదిక ముందస్తు వీక్షణ",
        "Select a report to preview": "ముందస్తు వీక్షణ కోసం ఒక నివేదికను ఎంచుకోండి",
        "Click on any report card above to generate a preview": "ప్రివ్యూ చూడటానికి పైన ఉన్న ఏదైనా కార్డ్‌పై క్లిక్ చేయండి",

        // Profile & Settings
        "Personal Information": "వ్యక్తిగత వివరాలు",
        "Full Name": "పూర్తి పేరు",
        "Email": "ఈమెయిల్",
        "Phone": "ఫోన్ నంబర్",
        "Phone Number": "ఫోన్ నంబర్",
        "Address": "చిరునామా",
        "Farm Name": "ఫార్మ్ / చెరువు పేరు",
        "Update Profile": "ప్రొఫైల్ నవీకరించండి",
        "Update Information": "వివరాలను నవీకరించండి",
        "Security Settings": "భద్రతా సెట్టింగ్‌లు",
        "Change Password": "పాస్‌వర్డ్ మార్చండి",
        "Current Password": "ప్రస్తుత పాస్‌వర్డ్",
        "New Password": "కొత్త పాస్‌వర్డ్",
        "Confirm Password": "పాస్‌వర్డ్ నిర్ధారించండి",
        "Save Password": "పాస్‌వర్డ్ సేవ్ చేయండి",
        "Enter your full name": "మీ పూర్తి పేరును నమోదు చేయండి",
        "Enter phone number": "ఫోన్ నంబర్‌ను నమోదు చేయండి",
        "Enter your address": "మీ చిరునామాను నమోదు చేయండి",
        "Enter farm name": "ఫార్మ్ పేరును నమోదు చేయండి",
        "Enter current password": "ప్రస్తుత పాస్‌వర్డ్‌ను నమోదు చేయండి",
        "Enter new password": "కొత్త పాస్‌వర్డ్‌ను నమోదు చేయండి",
        "Confirm new password": "కొత్త పాస్‌వర్డ్‌ను మళ్లీ నమోదు చేయండి",

        // Auth
        "Login": "లాగిన్",
        "Register": "రిజిస్టర్",
        "Sign Up": "సైన్ అప్",
        "Welcome Back!": "తిరిగి స్వాగతం!",
        "Login to continue to your account": "మీ ఖాతాలోకి ప్రవేశించడానికి లాగిన్ అవ్వండి",
        "Create an Account": "ఖాతాను సృష్టించండి",
        "Join AquaGuru today": "ఈరోజే AquaGuru లో చేరండి",
        "Email / Username": "ఈమెయిల్ / యూజర్ పేరు",
        "Password": "పాస్‌వర్డ్",
        "Forgot Password?": "పాస్‌వర్డ్ మర్చిపోయారా?",
        "Don't have an account?": "ఖాతా లేదా?",
        "Already have an account?": "ఇప్పటికే ఖాతా ఉందా?",
        "Login successful!": "లాగిన్ విజయవంతమైంది!",
        "Invalid username or password!": "చెల్లని యూజర్ పేరు లేదా పాస్‌వర్డ్!"
    };

    // Sort dictionary keys by length descending to match longer multi-word phrases first
    const sortedEnKeys = Object.keys(dictionary).sort((a, b) => b.length - a.length);

    // Generate reverse map (Telugu -> English)
    const reverseDictionary = {};
    for (const [en, te] of Object.entries(dictionary)) {
        reverseDictionary[te] = en;
    }
    const sortedTeKeys = Object.keys(reverseDictionary).sort((a, b) => b.length - a.length);

    // Get current language (default: check localStorage > cookie > 'en')
    function getCurrentLanguage() {
        if (localStorage.getItem('aqua_lang')) {
            return localStorage.getItem('aqua_lang');
        }
        const match = document.cookie.match(/(^|;)\s*lang\s*=\s*([^;]+)/);
        if (match && match[2]) {
            return match[2];
        }
        return 'en';
    }

    // Smart string translation with substring and phrase matching
    function translateString(text, targetLang) {
        if (!text || typeof text !== 'string') return text;
        const trimmed = text.trim();
        if (!trimmed) return text;

        if (targetLang === 'te') {
            // 1. Direct exact match
            if (dictionary[trimmed]) {
                return text.replace(trimmed, dictionary[trimmed]);
            }
            // 2. Direct with colon
            if (trimmed.endsWith(':') && dictionary[trimmed.slice(0, -1)]) {
                return text.replace(trimmed, dictionary[trimmed.slice(0, -1)] + ':');
            }
            // 3. Substring keyword replacement for composite badges (e.g., "+0 Active", "Today: 10 kg", "Avg ABW: 12g")
            let result = text;
            for (const key of sortedEnKeys) {
                if (key.length > 2 && result.includes(key)) {
                    result = result.split(key).join(dictionary[key]);
                }
            }
            return result;
        } else if (targetLang === 'en') {
            // 1. Direct exact match
            if (reverseDictionary[trimmed]) {
                return text.replace(trimmed, reverseDictionary[trimmed]);
            }
            // 2. Direct with colon
            if (trimmed.endsWith(':') && reverseDictionary[trimmed.slice(0, -1)]) {
                return text.replace(trimmed, reverseDictionary[trimmed.slice(0, -1)] + ':');
            }
            // 3. Substring keyword replacement
            let result = text;
            for (const key of sortedTeKeys) {
                if (key.length > 2 && result.includes(key)) {
                    result = result.split(key).join(reverseDictionary[key]);
                }
            }
            return result;
        }
        return text;
    }

    // Recursively translate all nodes in DOM
    function translateDOM(targetLang) {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function (node) {
                    if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_SKIP;
                    const parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_SKIP;
                    const tag = parent.tagName.toLowerCase();
                    if (tag === 'script' || tag === 'style' || tag === 'textarea' || parent.classList.contains('no-translate')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        const textNodes = [];
        while (walker.nextNode()) {
            textNodes.push(walker.currentNode);
        }

        textNodes.forEach(node => {
            node.nodeValue = translateString(node.nodeValue, targetLang);
        });

        // Translate placeholders
        document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(input => {
            const ph = input.getAttribute('placeholder');
            if (ph) {
                input.setAttribute('placeholder', translateString(ph, targetLang));
            }
        });

        // Translate select options
        document.querySelectorAll('select option').forEach(opt => {
            const txt = opt.textContent;
            if (txt && !opt.value.match(/^\d+$/)) {
                opt.textContent = translateString(txt, targetLang);
            }
        });

        // Translate button values & tooltips
        document.querySelectorAll('[title]').forEach(el => {
            const title = el.getAttribute('title');
            if (title) {
                el.setAttribute('title', translateString(title, targetLang));
            }
        });

        // Update dropdown label if present
        const label = document.getElementById('currentLangLabel');
        if (label) {
            label.textContent = targetLang === 'te' ? 'తెలుగు (Telugu)' : 'English';
        }
    }

    // Global Master Language Setter
    window.setAquaLanguage = function (targetLang) {
        if (targetLang !== 'en' && targetLang !== 'te') targetLang = 'en';

        // 1. Save locally
        try {
            localStorage.setItem('aqua_lang', targetLang);
        } catch (e) {}
        document.cookie = "lang=" + targetLang + "; path=/; max-age=31536000; SameSite=Lax";
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;";

        // 2. Instantly translate live DOM in 0 ms
        translateDOM(targetLang);

        // 3. Direct browser navigation for bulletproof mobile sync
        const nextUrl = window.location.pathname + window.location.search;
        const syncUrl = "/set-language/" + targetLang + "?next=" + encodeURIComponent(nextUrl) + "&_t=" + Date.now();
        window.location.href = syncUrl;
    };

    // Auto-initialize on page load
    document.addEventListener('DOMContentLoaded', function () {
        const activeLang = getCurrentLanguage();
        if (activeLang === 'te') {
            translateDOM('te');
        }

        // Set up MutationObserver for dynamically injected elements (e.g. Modals, Alerts, AJAX Tables)
        const observer = new MutationObserver(function (mutations) {
            const current = getCurrentLanguage();
            if (current === 'te') {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            node.nodeValue = translateString(node.nodeValue, 'te');
                        } else if (node.nodeType === Node.ELEMENT_NODE) {
                            const innerWalker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
                            while (innerWalker.nextNode()) {
                                innerWalker.currentNode.nodeValue = translateString(innerWalker.currentNode.nodeValue, 'te');
                            }
                        }
                    });
                });
            }
        });

        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    });

})();
