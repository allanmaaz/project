# Local Development Testing Guide

This guide explains how to test the core features of Clarify AI locally, including the new **AI Flood Detection & Rescue Dispatch** pipeline.

---

## 🖥️ 1. Access the Application
1.  **Frontend URL:** Open your browser and go to `http://localhost:3000`.
2.  **Backend URL:** The FastAPI server is running on `http://localhost:8000`. (You can view the interactive API documentation at `http://localhost:8000/docs`).

---

## 🔑 2. Authentication Test
1.  On the frontend (`http://localhost:3000`), you will be greeted by the login screen.
2.  Click **Sign In with Google**.
3.  Authenticate via your Google account. Once successful, Supabase will log you in and redirect you to the **Dashboard**.

---

## 🌊 3. Test the AI Flood & Rescue Dispatch Feature
To trigger the new domain-specific rescue dispatch pipeline:
1.  Prepare an emergency text snippet or image. You can copy-paste the text below into a `.txt` file or take a screenshot of it to upload:
    ```
    EMERGENCY DISASTER REPORT: Severe flooding in Zone A, Zone B, and near the High School.
    Water levels have breached the danger mark at 7.5 meters.
    An estimated 45 residents are reported stranded/trapped on rooftops.
    First responders from NDRF and Boat Squad 1 have been deployed.
    Emergency advisory: Boil all drinking water, stay off submersed roads, and avoid power lines.
    ```
2.  Go to the **Upload File** tab in the sidebar.
3.  Drag-and-drop or select your emergency file and click **Analyze**.
4.  **Watch the Progress:** The UI will show validation, storage uploading, OCR extraction, and AI processing in real-time.
5.  **View Results:** Once processing completes, it redirects to the analysis detail page. You will see:
    *   The **Severity Index Card** showing `7.5 / 10`.
    *   The **Est. Stranded Card** showing `45` persons.
    *   The **Dispatch Queue Board** showing priority targets (e.g. High School as Priority 1).
    *   The **Resource Allocation Matrix** showing active deployment status for *Boat Squad 1* and *NDRF*.
    *   The **Safety Advisories Box** displaying warnings.

---

## 💬 4. Interactive Q&A Chat
On the right-hand panel of the analysis detail page:
1.  Type a follow-up question (e.g., *"What safety advisories are listed?"* or *"Who is assigned to the High School rescue?"*).
2.  Hit **Send**. The response will stream back in real-time with context-aware disclaimers for disaster management.

---

## 📄 5. PDF Export & Download Authentication
1.  At the top-right of the analysis header, click **Export PDF**.
2.  The system will dynamically retrieve your Supabase JWT, authenticate the backend request, and download the compiled report (e.g., `ClarifyAI_Disaster_Rescue_Plan.pdf`) directly to your downloads folder.
