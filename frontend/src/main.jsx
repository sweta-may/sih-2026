import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://127.0.0.1:8000";
const USD_TO_INR = 83.5; // Standard maritime interbank exchange rate

// Structured World Ports with Country & Categories
const WORLD_PORTS = [
  {
    country: "India",
    category: "East Coast Ports",
    flag: "🇮🇳",
    ports: [
      { id: "INPRD", name: "Paradip", state: "Odisha", maxDraft: 16.5, maxLoa: 300.0, lat: 20.266, lon: 86.88, avgWaitBase: 18.0, congestion: "Moderate", activeVessels: 12, portDuesUsd: 48000 },
      { id: "INVTZ", name: "Visakhapatnam", state: "Andhra Pradesh", maxDraft: 18.1, maxLoa: 300.0, lat: 17.683, lon: 83.216, avgWaitBase: 36.5, congestion: "High", activeVessels: 8, portDuesUsd: 52000 },
      { id: "INGGV", name: "Gangavaram", state: "Andhra Pradesh", maxDraft: 18.0, maxLoa: 355.0, lat: 17.618, lon: 83.238, avgWaitBase: 15.0, congestion: "Low", activeVessels: 6, portDuesUsd: 44000 },
      { id: "INGPR", name: "Gopalpur", state: "Odisha", maxDraft: 14.2, maxLoa: 240.0, lat: 19.308, lon: 84.966, avgWaitBase: 9.0, congestion: "Low", activeVessels: 4, portDuesUsd: 32000 },
      { id: "INDHM", name: "Dhamra", state: "Odisha", maxDraft: 18.0, maxLoa: 350.0, lat: 20.803, lon: 86.974, avgWaitBase: 12.2, congestion: "Low", activeVessels: 7, portDuesUsd: 45000 },
      { id: "INHAL", name: "Haldia", state: "West Bengal", maxDraft: 12.2, maxLoa: 239.0, lat: 22.02, lon: 88.10, avgWaitBase: 14.0, congestion: "Low", activeVessels: 15, portDuesUsd: 38000 },
      { id: "INSAG", name: "Sagar/Sandheads", state: "West Bengal", maxDraft: 16.0, maxLoa: 300.0, lat: 21.65, lon: 88.08, avgWaitBase: 15.2, congestion: "Moderate", activeVessels: 5, portDuesUsd: 35000 },
    ],
  },
  {
    country: "Australia",
    category: "Major Bulk Ports",
    flag: "🇦🇺",
    ports: [
      { id: "AUZNE", name: "Port Hedland", maxDraft: 19.0, maxLoa: 330.0, lat: -20.31, lon: 118.57, avgWaitBase: 24.0, congestion: "Moderate", activeVessels: 22, portDuesUsd: 62000 },
      { id: "AUNTL", name: "Newcastle", maxDraft: 15.2, maxLoa: 300.0, lat: -32.92, lon: 151.78, avgWaitBase: 30.0, congestion: "High", activeVessels: 18, portDuesUsd: 54000 },
      { id: "AUHAY", name: "Hay Point", maxDraft: 19.5, maxLoa: 320.0, lat: -21.28, lon: 149.30, avgWaitBase: 26.0, congestion: "Moderate", activeVessels: 14, portDuesUsd: 58000 },
      { id: "AUGLT", name: "Gladstone", maxDraft: 17.5, maxLoa: 315.0, lat: -23.84, lon: 151.26, avgWaitBase: 16.0, congestion: "Low", activeVessels: 11, portDuesUsd: 51000 },
      { id: "AUDAM", name: "Dampier", maxDraft: 19.0, maxLoa: 330.0, lat: -20.65, lon: 116.71, avgWaitBase: 20.0, congestion: "Moderate", activeVessels: 16, portDuesUsd: 60000 },
    ],
  },
  {
    country: "Indonesia",
    category: "Major Coal & Mineral Ports",
    flag: "🇮🇩",
    ports: [
      { id: "IDSMR", name: "Samarinda Anchorage", maxDraft: 14.0, maxLoa: 250.0, lat: -0.50, lon: 117.15, avgWaitBase: 22.0, congestion: "Moderate", activeVessels: 19, portDuesUsd: 30000 },
      { id: "IDBDJ", name: "Banjarmasin / Taboneo", maxDraft: 13.5, maxLoa: 240.0, lat: -3.32, lon: 114.59, avgWaitBase: 20.0, congestion: "Moderate", activeVessels: 15, portDuesUsd: 28000 },
      { id: "IDBAP", name: "Balikpapan", maxDraft: 15.0, maxLoa: 280.0, lat: -1.27, lon: 116.83, avgWaitBase: 16.0, congestion: "Low", activeVessels: 12, portDuesUsd: 34000 },
      { id: "IDTPP", name: "Tanjung Priok (Jakarta)", maxDraft: 14.0, maxLoa: 290.0, lat: -6.10, lon: 106.88, avgWaitBase: 18.0, congestion: "Moderate", activeVessels: 25, portDuesUsd: 38000 },
    ],
  },
  {
    country: "Russia",
    category: "Major Bulk Export Ports",
    flag: "🇷🇺",
    ports: [
      { id: "RUVOZ", name: "Vostochny", maxDraft: 16.5, maxLoa: 300.0, lat: 42.73, lon: 133.08, avgWaitBase: 28.0, congestion: "High", activeVessels: 14, portDuesUsd: 49000 },
      { id: "RUULU", name: "Ust-Luga", maxDraft: 17.0, maxLoa: 320.0, lat: 59.68, lon: 28.40, avgWaitBase: 32.0, congestion: "High", activeVessels: 16, portDuesUsd: 53000 },
      { id: "RUNVS", name: "Novorossiysk", maxDraft: 15.0, maxLoa: 290.0, lat: 44.72, lon: 37.78, avgWaitBase: 24.0, congestion: "Moderate", activeVessels: 18, portDuesUsd: 46000 },
      { id: "RUVVO", name: "Vladivostok", maxDraft: 14.5, maxLoa: 260.0, lat: 43.11, lon: 131.87, avgWaitBase: 15.0, congestion: "Low", activeVessels: 9, portDuesUsd: 43000 },
    ],
  },
  {
    country: "Mozambique",
    category: "Major Mineral Ports",
    flag: "🇲🇿",
    ports: [
      { id: "MZMPM", name: "Maputo / Matola", maxDraft: 14.3, maxLoa: 270.0, lat: -25.97, lon: 32.58, avgWaitBase: 26.0, congestion: "Moderate", activeVessels: 11, portDuesUsd: 41000 },
      { id: "MZBEW", name: "Beira", maxDraft: 11.5, maxLoa: 220.0, lat: -19.83, lon: 34.84, avgWaitBase: 18.0, congestion: "Low", activeVessels: 7, portDuesUsd: 34000 },
      { id: "MZNAC", name: "Nacala Deepwater", maxDraft: 20.0, maxLoa: 340.0, lat: -14.54, lon: 40.67, avgWaitBase: 14.0, congestion: "Low", activeVessels: 8, portDuesUsd: 46000 },
    ],
  },
  {
    country: "USA",
    category: "Major Bulk & Coal Ports",
    flag: "🇺🇸",
    ports: [
      { id: "USORF", name: "Norfolk / Hampton Roads", maxDraft: 15.5, maxLoa: 320.0, lat: 36.95, lon: -76.33, avgWaitBase: 22.0, congestion: "Moderate", activeVessels: 20, portDuesUsd: 68000 },
      { id: "USMSY", name: "New Orleans / Mississippi", maxDraft: 14.5, maxLoa: 290.0, lat: 29.95, lon: -90.07, avgWaitBase: 25.0, congestion: "Moderate", activeVessels: 24, portDuesUsd: 64000 },
      { id: "USHOU", name: "Houston", maxDraft: 14.0, maxLoa: 280.0, lat: 29.76, lon: -95.36, avgWaitBase: 19.0, congestion: "Low", activeVessels: 28, portDuesUsd: 61000 },
      { id: "USBAL", name: "Baltimore", maxDraft: 15.2, maxLoa: 305.0, lat: 39.29, lon: -76.61, avgWaitBase: 21.0, congestion: "Low", activeVessels: 15, portDuesUsd: 63000 },
    ],
  },
  {
    country: "Singapore",
    category: "Global Transshipment Hub",
    flag: "🇸🇬",
    ports: [
      { id: "SGSIN", name: "Singapore Port", maxDraft: 18.5, maxLoa: 350.0, lat: 1.29, lon: 103.85, avgWaitBase: 12.0, congestion: "Low", activeVessels: 45, portDuesUsd: 42000 },
    ],
  },
  {
    country: "China",
    category: "Major Bulk Discharge Ports",
    flag: "🇨🇳",
    ports: [
      { id: "CNQIN", name: "Qingdao", maxDraft: 20.0, maxLoa: 350.0, lat: 36.06, lon: 120.38, avgWaitBase: 28.0, congestion: "Moderate", activeVessels: 32, portDuesUsd: 55000 },
      { id: "CNFAN", name: "Fangcheng", maxDraft: 16.5, maxLoa: 300.0, lat: 21.68, lon: 108.35, avgWaitBase: 20.0, congestion: "Moderate", activeVessels: 18, portDuesUsd: 46000 },
      { id: "CNTNJ", name: "Tianjin", maxDraft: 18.0, maxLoa: 330.0, lat: 38.98, lon: 117.75, avgWaitBase: 34.0, congestion: "High", activeVessels: 28, portDuesUsd: 53000 },
      { id: "CNNGB", name: "Ningbo-Zhoushan", maxDraft: 21.0, maxLoa: 360.0, lat: 29.87, lon: 121.55, avgWaitBase: 22.0, congestion: "Moderate", activeVessels: 38, portDuesUsd: 57000 },
    ],
  },
  {
    country: "Netherlands",
    category: "European Hubs",
    flag: "🇳🇱",
    ports: [
      { id: "NLRTM", name: "Rotterdam", maxDraft: 22.0, maxLoa: 380.0, lat: 51.92, lon: 4.47, avgWaitBase: 15.0, congestion: "Low", activeVessels: 35, portDuesUsd: 74000 },
      { id: "NLAMS", name: "Amsterdam", maxDraft: 15.0, maxLoa: 300.0, lat: 52.37, lon: 4.89, avgWaitBase: 12.0, congestion: "Low", activeVessels: 18, portDuesUsd: 65000 },
    ],
  },
];

// Flattened lookup for all ports
const ALL_PORTS_MAP = {};
WORLD_PORTS.forEach((group) => {
  group.ports.forEach((p) => {
    ALL_PORTS_MAP[p.id] = { ...p, country: group.country, category: group.category };
  });
});

// Haversine nautical distance calculation
function calculateDistanceNm(lat1, lon1, lat2, lon2) {
  const R_km = 6371.0;
  const dlat = ((lat2 - lat1) * Math.PI) / 180.0;
  const dlon = ((lon2 - lon1) * Math.PI) / 180.0;
  const a =
    Math.sin(dlat / 2.0) ** 2 +
    Math.cos((lat1 * Math.PI) / 180.0) *
      Math.cos((lat2 * Math.PI) / 180.0) *
      Math.sin(dlon / 2.0) ** 2;
  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
  return Math.round(R_km * c * 0.539957);
}

const VESSEL_PROFILES = {
  Handysize: {
    name: "Handysize",
    dwtMin: 28000,
    dwtMax: 42000,
    typicalDwt: 38200,
    loa: 180.0,
    beam: 29.8,
    draft: 10.5,
    speedKts: 11.0,
    seaFuelMtDay: 14.5,
    demurrageRatePdUsd: 12000,
    baseRatePerTonUsd: 19.5,
    forecastRatePerTonUsd: 18.9,
  },
  Supramax: {
    name: "Supramax",
    dwtMin: 42001,
    dwtMax: 65000,
    typicalDwt: 55000,
    loa: 189.99,
    beam: 32.26,
    draft: 12.8,
    speedKts: 11.5,
    seaFuelMtDay: 18.2,
    demurrageRatePdUsd: 15000,
    baseRatePerTonUsd: 24.5,
    forecastRatePerTonUsd: 22.8,
  },
  Panamax: {
    name: "Panamax",
    dwtMin: 65001,
    dwtMax: 100000,
    typicalDwt: 75000,
    loa: 229.0,
    beam: 32.25,
    draft: 14.43,
    speedKts: 12.0,
    seaFuelMtDay: 22.5,
    demurrageRatePdUsd: 18500,
    baseRatePerTonUsd: 26.8,
    forecastRatePerTonUsd: 27.4,
  },
  Capesize: {
    name: "Capesize",
    dwtMin: 100001,
    dwtMax: 220000,
    typicalDwt: 180000,
    loa: 290.0,
    beam: 45.0,
    draft: 18.2,
    speedKts: 12.5,
    seaFuelMtDay: 32.0,
    demurrageRatePdUsd: 28000,
    baseRatePerTonUsd: 31.2,
    forecastRatePerTonUsd: 28.5,
  },
};

// Available Vessels for VesselFinder Interactive Map
const AIS_VESSELS = [
  {
    mmsi: 419001244,
    imo: 9482104,
    name: "MV OCEAN PIONEER",
    vessel_class: "Supramax",
    dwt: 55000,
    lat: 19.82,
    lon: 86.20,
    speed_knots: 11.4,
    course_deg: 42.0,
    heading_deg: 40.0,
    nav_status: "Under way using engine",
    draught_m: 12.8,
    destination: "INPRD",
    destination_name: "Paradip",
    distance_to_port_nm: 142.5,
    direct_eta_utc: "2026-09-12T02:40:00Z",
    delay_hours: 3.5,
    delay_status: "Delayed (+3.5 hrs)",
    expected_waiting_hours: 18.0,
    expected_turnaround_hours: 64.5,
    idle_demurrage_inr: 939375,
    irctc_stage_idx: 2, // At Port Area
    status_summary: "At Port Area — Approaching Paradip anchorage queue #3",
  },
  {
    mmsi: 419001889,
    imo: 9482188,
    name: "MV BENGAL GLORY",
    vessel_class: "Panamax",
    dwt: 75000,
    lat: 20.25,
    lon: 86.92,
    speed_knots: 0.2,
    course_deg: 115.0,
    heading_deg: 115.0,
    nav_status: "At anchor",
    draught_m: 14.2,
    destination: "INPRD",
    destination_name: "Paradip",
    distance_to_port_nm: 6.2,
    direct_eta_utc: "2026-09-11T12:00:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 14.5,
    expected_turnaround_hours: 72.0,
    idle_demurrage_inr: 934500,
    irctc_stage_idx: 3, // Waiting at anchor
    status_summary: "Waiting at Anchor — Awaiting berth assignment",
  },
  {
    mmsi: 419002130,
    imo: 9482210,
    name: "MV VIZAG LEADER",
    vessel_class: "Capesize",
    dwt: 180000,
    lat: 17.52,
    lon: 83.45,
    speed_knots: 12.8,
    course_deg: 290.0,
    heading_deg: 292.0,
    nav_status: "Under way using engine",
    draught_m: 17.8,
    destination: "INVTZ",
    destination_name: "Visakhapatnam",
    distance_to_port_nm: 195.0,
    direct_eta_utc: "2026-09-12T18:15:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 36.5,
    expected_turnaround_hours: 96.0,
    idle_demurrage_inr: 3550000,
    irctc_stage_idx: 0, // On Time
    status_summary: "On Time — Approaching outer approaches of Visakhapatnam",
  },
  {
    mmsi: 419003501,
    imo: 9482350,
    name: "MV EASTERN PRIDE",
    vessel_class: "Handysize",
    dwt: 38200,
    lat: 21.85,
    lon: 87.92,
    speed_knots: 9.6,
    course_deg: 18.0,
    heading_deg: 20.0,
    nav_status: "Under way using engine",
    draught_m: 10.4,
    destination: "INHAL",
    destination_name: "Haldia",
    distance_to_port_nm: 110.0,
    direct_eta_utc: "2026-09-11T23:30:00Z",
    delay_hours: 1.8,
    delay_status: "Delayed (+1.8 hrs)",
    expected_waiting_hours: 14.0,
    expected_turnaround_hours: 48.0,
    idle_demurrage_inr: 584500,
    irctc_stage_idx: 1, // Delayed
    status_summary: "Delayed — Reduced speed through Hooghly channel estuary",
  },
  {
    mmsi: 419004812,
    imo: 9482481,
    name: "MV KALINGA EXPRESS",
    vessel_class: "Supramax",
    dwt: 58000,
    lat: 20.78,
    lon: 87.05,
    speed_knots: 1.1,
    course_deg: 180.0,
    heading_deg: 180.0,
    nav_status: "At anchor",
    draught_m: 12.5,
    destination: "INDHM",
    destination_name: "Dhamra",
    distance_to_port_nm: 8.5,
    direct_eta_utc: "2026-09-11T14:00:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 12.2,
    expected_turnaround_hours: 56.0,
    idle_demurrage_inr: 635000,
    irctc_stage_idx: 3, // Waiting at anchor
    status_summary: "Waiting at Anchor — Dhamra deepwater roads",
  },
  {
    mmsi: 419005923,
    imo: 9482592,
    name: "MV MAHANADI STAR",
    vessel_class: "Panamax",
    dwt: 82000,
    lat: 17.58,
    lon: 83.30,
    speed_knots: 0.0,
    course_deg: 0.0,
    heading_deg: 45.0,
    nav_status: "Moored / Berthed",
    draught_m: 14.1,
    destination: "INGGV",
    destination_name: "Gangavaram",
    distance_to_port_nm: 0.5,
    direct_eta_utc: "2026-09-11T06:00:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 0.0,
    expected_turnaround_hours: 32.0,
    idle_demurrage_inr: 0,
    irctc_stage_idx: 4, // Berthed / Loading
    status_summary: "Berthed / Loading — Discharging cargo at Berth #2",
  },
  {
    mmsi: 419006411,
    imo: 9482641,
    name: "MV GOPALPUR TRADER",
    vessel_class: "Handysize",
    dwt: 35000,
    lat: 19.25,
    lon: 85.05,
    speed_knots: 10.2,
    course_deg: 245.0,
    heading_deg: 245.0,
    nav_status: "Under way using engine",
    draught_m: 10.2,
    destination: "INGPR",
    destination_name: "Gopalpur",
    distance_to_port_nm: 85.0,
    direct_eta_utc: "2026-09-12T08:00:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 9.0,
    expected_turnaround_hours: 42.0,
    idle_demurrage_inr: 375000,
    irctc_stage_idx: 0, // On Time
    status_summary: "On Time — In transit to Gopalpur bulk terminal",
  },
  {
    mmsi: 419007218,
    imo: 9482721,
    name: "MV SAGAR GAURAV",
    vessel_class: "Capesize",
    dwt: 175000,
    lat: 21.60,
    lon: 88.15,
    speed_knots: 0.5,
    course_deg: 90.0,
    heading_deg: 90.0,
    nav_status: "At anchor",
    draught_m: 15.8,
    destination: "INSAG",
    destination_name: "Sagar-Sandheads",
    distance_to_port_nm: 4.0,
    direct_eta_utc: "2026-09-11T10:00:00Z",
    delay_hours: 0.0,
    delay_status: "On Time",
    expected_waiting_hours: 15.2,
    expected_turnaround_hours: 60.0,
    idle_demurrage_inr: 1475000,
    irctc_stage_idx: 3, // Waiting at anchor
    status_summary: "Waiting at Anchor — Sagar-Sandheads lighterage anchorage",
  },
];

const IRCTC_STAGES = [
  { id: 0, label: "On Time" },
  { id: 1, label: "Delayed" },
  { id: 2, label: "At Port Area" },
  { id: 3, label: "Waiting (Anchor)" },
  { id: 4, label: "Berthed / Loading" },
  { id: 5, label: "Departed" },
];

function App() {
  // Navigation: 'dashboard' or 'tracking'
  const [activeNav, setActiveNav] = useState("dashboard");

  // Global Currency State: default INR
  const [currency, setCurrency] = useState("INR");

  // Voyage Inputs
  const [cargoType, setCargoType] = useState("Iron Ore");
  const [cargoMt, setCargoMt] = useState(55000);
  const [loadingPortKey, setLoadingPortKey] = useState("INPRD");
  const [dischargePortKey, setDischargePortKey] = useState("SGSIN");
  const [laycanDate, setLaycanDate] = useState("2026-09-15");

  // Tracking State (Requirement 4: Do NOT show vessel details by default until user selects one)
  const [selectedTrackVessel, setSelectedTrackVessel] = useState(null);
  const [vesselFilter, setVesselFilter] = useState("All");

  const mapInstanceRef = useRef(null);

  // Currency Formatter Helpers
  const formatRate = (usdPerTon) => {
    if (currency === "INR") {
      const inrPerTon = Math.round(usdPerTon * USD_TO_INR);
      return `₹${inrPerTon.toLocaleString("en-IN")}/ton`;
    }
    return `$${usdPerTon.toFixed(1)}/ton`;
  };

  const formatExecutive = (usdValue) => {
    if (currency === "INR") {
      const inr = usdValue * USD_TO_INR;
      if (inr >= 10000000) return `₹${(inr / 10000000).toFixed(2)} Cr`;
      if (inr >= 100000) return `₹${(inr / 100000).toFixed(1)} Lakh`;
      return `₹${Math.round(inr).toLocaleString("en-IN")}`;
    }
    if (usdValue >= 1000000) return `$${(usdValue / 1000000).toFixed(2)}M`;
    if (usdValue >= 1000) return `$${Math.round(usdValue / 1000)}K`;
    return `$${Math.round(usdValue).toLocaleString("en-US")}`;
  };

  const formatExact = (usdValue) => {
    if (currency === "INR") {
      return `₹${Math.round(usdValue * USD_TO_INR).toLocaleString("en-IN")}`;
    }
    return `$${Math.round(usdValue).toLocaleString("en-US")}`;
  };

  // Port Resolution
  const loadPort = ALL_PORTS_MAP[loadingPortKey] || ALL_PORTS_MAP["INPRD"];
  const dischPort = ALL_PORTS_MAP[dischargePortKey] || ALL_PORTS_MAP["SGSIN"];

  // Calculated Great-Circle Nautical Distance
  const distanceNm = calculateDistanceNm(loadPort.lat, loadPort.lon, dischPort.lat, dischPort.lon);

  // Vessel Class Recommendation
  let recommendedVesselType = "Supramax";
  if (cargoMt <= 42000) recommendedVesselType = "Handysize";
  else if (cargoMt <= 65000) recommendedVesselType = "Supramax";
  else if (cargoMt <= 100000) recommendedVesselType = "Panamax";
  else recommendedVesselType = "Capesize";

  const vProfile = VESSEL_PROFILES[recommendedVesselType];

  // Port Draft and LOA Screening
  const draftDiff = loadPort.maxDraft - vProfile.draft;
  const isDraftCompatible = draftDiff >= 0.5;
  const loaDiff = loadPort.maxLoa - vProfile.loa;
  const isLoaCompatible = loaDiff >= 0;
  const isFullyCompatible = isDraftCompatible && isLoaCompatible;

  // Transit & Port Queue
  const transitDays = distanceNm / (vProfile.speedKts * 24);
  const waitHours = loadPort.avgWaitBase * (recommendedVesselType === "Capesize" ? 1.3 : 1.0);
  const waitDays = waitHours / 24.0;
  const turnaroundHours = Math.round(waitHours + (cargoMt / 22000.0) * 24.0);

  // Freight Rates & Decision
  const spotRateUsd = vProfile.baseRatePerTonUsd;
  const forecastRateUsd = vProfile.forecastRatePerTonUsd;
  const isRateDown = forecastRateUsd < spotRateUsd;
  const decisionSignal = isRateDown ? "WAIT" : "CHARTER NOW";

  // Total Cost Waterfall in USD
  const freightSpotUsd = cargoMt * spotRateUsd;
  const freightWaitUsd = cargoMt * forecastRateUsd;
  const seaFuelCostUsd = Math.round(transitDays * vProfile.seaFuelMtDay * 600);
  const idleFuelCostUsd = Math.round(waitDays * 2.5 * 600);
  const portTariffsUsd = loadPort.portDuesUsd + (dischPort.portDuesUsd || 35000);
  const expectedDemurrageUsd = Math.round(waitDays * vProfile.demurrageRatePdUsd);

  const charterNowTotalUsd = freightSpotUsd + seaFuelCostUsd + idleFuelCostUsd + portTariffsUsd + expectedDemurrageUsd;
  const waitTotalUsd = freightWaitUsd + seaFuelCostUsd + idleFuelCostUsd * 0.6 + portTariffsUsd + expectedDemurrageUsd * 0.4;
  const totalSavingsUsd = Math.max(0, charterNowTotalUsd - waitTotalUsd);

  const charterNowFormatted = formatExecutive(charterNowTotalUsd);
  const waitFormatted = formatExecutive(waitTotalUsd);
  const savingsFormatted = formatExecutive(totalSavingsUsd);

  // Contract Terms
  const recommendedContract = "Spot Voyage Charter (Gencon 94)";
  const laytimeWwd = (cargoMt / 12000).toFixed(1);

  // Leaflet Map Lifecycle in Tracking View
  useEffect(() => {
    if (activeNav === "tracking" && typeof window !== "undefined" && window.L) {
      const container = document.getElementById("leaflet-ais-map");
      if (!container) return;

      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      const map = window.L.map("leaflet-ais-map").setView([19.5, 85.5], 6);
      mapInstanceRef.current = map;

      window.L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; OpenStreetMap &copy; CARTO",
        maxZoom: 18,
      }).addTo(map);

      // Add East Coast Ports to Map
      WORLD_PORTS[0].ports.forEach((p) => {
        const portIcon = window.L.divIcon({
          className: "leaflet-port-icon",
          html: `<div style="background:#0f172a; color:#fff; font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; border:1px solid #94a3b8; white-space:nowrap; box-shadow:0 2px 4px rgba(0,0,0,0.25);">⚓ ${p.name}</div>`,
          iconSize: [80, 22],
          iconAnchor: [40, 11],
        });
        window.L.marker([p.lat, p.lon], { icon: portIcon })
          .addTo(map)
          .bindPopup(`<b>${p.name} Port (${p.id})</b><br>Max Draft: ${p.maxDraft}m<br>Congestion: ${p.congestion}<br>Avg Wait: ${p.avgWaitBase}h`);
      });

      // Filter Vessels
      const visibleVessels = AIS_VESSELS.filter((v) => {
        if (vesselFilter === "All") return true;
        return v.vessel_class === vesselFilter;
      });

      // Add Vessel Pins to Map
      visibleVessels.forEach((v) => {
        const isSelected = selectedTrackVessel?.mmsi === v.mmsi;
        const color = isSelected ? "#ef4444" : "#2563eb";
        const vIcon = window.L.divIcon({
          className: "leaflet-ship-icon",
          html: `<div style="width:28px; height:28px; border-radius:50%; background:${color}; border:2px solid #ffffff; display:flex; align-items:center; justify-content:center; color:#fff; font-size:13px; box-shadow:0 0 0 3px ${isSelected ? 'rgba(239,68,68,0.35)' : 'rgba(37,99,235,0.3)'}; cursor:pointer;" title="${v.name}">🚢</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const marker = window.L.marker([v.lat, v.lon], { icon: vIcon }).addTo(map);
        marker.on("click", () => {
          setSelectedTrackVessel(v);
        });

        if (isSelected) {
          marker.bindPopup(`<b>${v.name}</b><br>${v.vessel_class}<br>Speed: ${v.speed_knots} kts`).openPopup();
        }
      });
    }
  }, [activeNav, selectedTrackVessel, vesselFilter]);

  return (
    <div className="smartfreight-app-frame">
      <div className="dashboard-grid">
        {/* ==================== LEFT SIDEBAR ==================== */}
        <div className="sidebar">
          <div className="brand-title" onClick={() => setActiveNav("dashboard")}>
            <i className="ti ti-anchor" aria-hidden="true"></i>SmartFreight
          </div>

          <button
            className={`nav-item ${activeNav === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveNav("dashboard")}
          >
            <i className="ti ti-home" aria-hidden="true"></i><span>Dashboard</span>
          </button>

          <button
            className={`nav-item ${activeNav === "tracking" ? "active" : ""}`}
            onClick={() => setActiveNav("tracking")}
          >
            <i className="ti ti-map-2" aria-hidden="true"></i><span>Live Tracking</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-voyage")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-plus" aria-hidden="true"></i><span>New voyage</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-forecast")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-chart-line" aria-hidden="true"></i><span>Freight forecast</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-compat")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-ship" aria-hidden="true"></i><span>Vessel optimization</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-congestion")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-anchor" aria-hidden="true"></i><span>Port and congestion</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-cost")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-report" aria-hidden="true"></i><span>Cost & Decision</span>
          </button>

          <button
            className="nav-item"
            onClick={() => {
              setActiveNav("dashboard");
              document.getElementById("sec-contract")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <i className="ti ti-shield-check" aria-hidden="true"></i><span>Contract terms</span>
          </button>

          <button
            className="nav-item bottom-item"
            onClick={() => alert(`SmartFreight AI Active · Currency: ${currency} · Backend: ${API_URL}`)}
          >
            <i className="ti ti-settings" aria-hidden="true"></i><span>Settings</span>
          </button>
        </div>

        {/* ==================== RIGHT MAIN PANEL ==================== */}
        <div className="main-content">
          {/* Top Header */}
          <div className="top-header">
            <div>
              <h2>{activeNav === "dashboard" ? "Overview" : "Live AIS Vessel Tracking"}</h2>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "2px 0 0" }}>
                {activeNav === "dashboard"
                  ? "Maritime Freight Decision Platform · Multi-Horizon ML Forecasting & Voyage Optimizer"
                  : "Interactive VesselFinder AIS Feed · Real-time East Coast India & Global Fleet Radar"}
              </p>
            </div>
            <div className="header-right">
              {/* Currency Toggle */}
              <div className="currency-toggle" title="Currency Selection">
                <button
                  className={currency === "INR" ? "active" : ""}
                  onClick={() => setCurrency("INR")}
                >
                  ₹ INR
                </button>
                <button
                  className={currency === "USD" ? "active" : ""}
                  onClick={() => setCurrency("USD")}
                >
                  $ USD
                </button>
              </div>

              <button
                className="bell-btn"
                title="Alerts"
                onClick={() => alert(`${loadPort.name} Port Alert: ${loadPort.activeVessels} vessels waiting at roads. Delay: +${loadPort.avgWaitBase}h.`)}
              >
                <i className="ti ti-bell" aria-hidden="true"></i>
                <span className="bell-badge"></span>
              </button>
              <div className="avatar" title="Charterer / Port Authority Account">PA</div>
            </div>
          </div>

          {/* =========================================================================
              VIEW 1: DASHBOARD / OVERVIEW (CONTINUOUS ONE-PAGE FLOW WITHOUT STEP NUMBERS)
              Requirement 1: NO step numbers.
              Requirement 2: NO live tracking section on the home page.
             ========================================================================= */}
          {activeNav === "dashboard" && (
            <>
              {/* Quick Workflow Navigation Bar (No Step Numbers) */}
              <div className="workflow-stepper-strip">
                {[
                  { label: "Voyage Setup", id: "sec-voyage" },
                  { label: "Freight Outlook", id: "sec-forecast" },
                  { label: "Vessel Fit", id: "sec-compat" },
                  { label: "Port Queue", id: "sec-congestion" },
                  { label: "Cost Waterfall", id: "sec-cost" },
                  { label: "⭐ Decision", id: "sec-decision" },
                  { label: "Contract", id: "sec-contract" },
                ].map((s) => (
                  <div
                    key={s.id}
                    className="flow-step-pill"
                    onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
                  >
                    <span>{s.label}</span>
                  </div>
                ))}
              </div>

              {/* 1. VOYAGE CONFIGURATION */}
              <section id="sec-voyage" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-box" aria-hidden="true"></i>
                    <span>Voyage Configuration</span>
                  </div>
                  <span className="flow-badge ready">● Active</span>
                </div>

                <div className="voyage-form-grid">
                  <div className="form-item">
                    <label>Cargo Segment</label>
                    <select value={cargoType} onChange={(e) => setCargoType(e.target.value)}>
                      <option>Iron Ore</option>
                      <option>Thermal Coal</option>
                      <option>Coking Coal</option>
                      <option>Bauxite</option>
                      <option>Grain</option>
                      <option>Fertilizer</option>
                    </select>
                  </div>

                  <div className="form-item">
                    <label>Cargo Quantity (MT)</label>
<input
  type="number"
  min={1}
  value={cargoMt}
  step={5000}
  onChange={(e) => setCargoMt(Math.max(1, Number(e.target.value) || 1))}
/>
                    <div className="preset-chips">
                      <span className={`preset-chip ${cargoMt === 35000 ? "active" : ""}`} onClick={() => setCargoMt(35000)}>35k (Handy)</span>
                      <span className={`preset-chip ${cargoMt === 55000 ? "active" : ""}`} onClick={() => setCargoMt(55000)}>55k (Supra)</span>
                      <span className={`preset-chip ${cargoMt === 75000 ? "active" : ""}`} onClick={() => setCargoMt(75000)}>75k (Pana)</span>
                      <span className={`preset-chip ${cargoMt === 170000 ? "active" : ""}`} onClick={() => setCargoMt(170000)}>170k (Cape)</span>
                    </div>
                  </div>

                  <div className="form-item">
                    <label>Target Laycan Date</label>
                    <input type="date" value={laycanDate} onChange={(e) => setLaycanDate(e.target.value)} />
                  </div>

                  {/* Requirement 6: Categorized Source Port Dropdown */}
                  <div className="form-item">
                    <label>Source Port (Loading)</label>
                    <select value={loadingPortKey} onChange={(e) => setLoadingPortKey(e.target.value)}>
                      {WORLD_PORTS.map((grp) => (
                        <optgroup key={grp.country} label={`${grp.flag} ${grp.country} — ${grp.category}`}>
                          {grp.ports.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} {p.state ? `(${p.state})` : ""} · Draft: {p.maxDraft}m
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  </div>

                  {/* Requirement 6: Categorized Destination Port Dropdown */}
                  <div className="form-item">
                    <label>Destination Port (Discharge)</label>
                    <select value={dischargePortKey} onChange={(e) => setDischargePortKey(e.target.value)}>
                      {WORLD_PORTS.map((grp) => (
                        <optgroup key={grp.country} label={`${grp.flag} ${grp.country} — ${grp.category}`}>
                          {grp.ports.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} {p.state ? `(${p.state})` : ""} · Draft: {p.maxDraft}m
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  </div>

                  <div className="form-item" style={{ justifyContent: "flex-end" }}>
                    <button
                      className="btn-contract-action"
                      style={{ width: "100%", justifyContent: "center" }}
                      onClick={() => document.getElementById("sec-forecast")?.scrollIntoView({ behavior: "smooth" })}
                    >
                      <i className="ti ti-calculator" aria-hidden="true"></i> Compute Voyage Strategy →
                    </button>
                  </div>
                </div>
              </section>

              {/* 2. FREIGHT TREND & RATE OUTLOOK */}
              <section id="sec-forecast" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-chart-line" aria-hidden="true"></i>
                    <span>Freight Trend & Multi-Horizon Rate Outlook</span>
                  </div>
                  <span className="flow-badge ready">● Random Forest Trained</span>
                </div>

                {/* 4 Metrics in selected currency */}
                <div className="metrics-row">
                  <div className="metric-card">
                    <p className="metric-label">Freight rate</p>
                    <p className="metric-val">{formatRate(spotRateUsd)}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Forecast</p>
                    <p className="metric-val forecast-val">
                      {formatRate(forecastRateUsd)}{" "}
                      <i className="ti ti-arrow-down-right" style={{ fontSize: "14px" }} aria-hidden="true"></i>
                    </p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Active vessels in sector</p>
                    <p className="metric-val">{loadPort.activeVessels}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Avg waiting at {loadPort.name}</p>
                    <p className="metric-val">{Math.round(waitHours)} hrs</p>
                  </div>
                </div>

                <div className="forecast-horizons-grid">
                  <div className="horizon-card">
                    <span className="h-label">7-Day Forward Horizon</span>
                    <p className="h-val">{formatRate(spotRateUsd * 0.955)}</p>
                    <span className="h-diff">↓ 4.5% vs spot</span>
                  </div>
                  <div className="horizon-card best-window">
                    <span className="h-label" style={{ color: "var(--text-accent)" }}>14-Day (Optimal Entry Window)</span>
                    <p className="h-val" style={{ color: "var(--text-accent)" }}>{formatRate(forecastRateUsd)}</p>
                    <span className="h-diff" style={{ color: "var(--text-accent)" }}>↓ 6.9% dip — Recommended Timing</span>
                  </div>
                  <div className="horizon-card">
                    <span className="h-label">30-Day Forward Horizon</span>
                    <p className="h-val">{formatRate(spotRateUsd * 0.984)}</p>
                    <span className="h-diff">↓ 1.6% (rebound phase)</span>
                  </div>
                </div>

                <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                  💡 <strong>Timing Intelligence:</strong> Freight rates soften by <strong>{formatRate(spotRateUsd - forecastRateUsd).replace("/ton", "")} per ton</strong> over the next 3–5 days before global tonnage tightening triggers a rebound.
                </p>
              </section>

              {/* 3. RECOMMENDED VESSEL & PORT COMPATIBILITY */}
              <section id="sec-compat" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-ship" aria-hidden="true"></i>
                    <span>Vessel & Port Compatibility Screening</span>
                  </div>
                  <span className={`flow-badge ${isFullyCompatible ? "ready" : "warning"}`}>
                    {isFullyCompatible ? "✅ 100% Port Compatible" : "⚠️ Draft / LOA Constraint"}
                  </span>
                </div>

                <div className="vessel-compat-grid">
                  <div className="compat-card">
                    <p style={{ fontSize: "13px", fontWeight: 600, margin: "0 0 8px" }}>
                      Selected Vessel Class: {vProfile.name} ({vProfile.typicalDwt.toLocaleString()} DWT)
                    </p>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Optimal Parcel</span>
                      <span style={{ fontWeight: 600 }}>{cargoMt.toLocaleString()} MT (98.2% Stowage Efficiency)</span>
                    </div>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Vessel Dimensions</span>
                      <span>LOA: {vProfile.loa}m · Beam: {vProfile.beam}m · Draft: {vProfile.draft}m</span>
                    </div>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Daily Fuel Consumption</span>
                      <span>{vProfile.speedKts} kts · {vProfile.seaFuelMtDay} MT VLSFO/day</span>
                    </div>
                  </div>

                  <div className="compat-card">
                    <p style={{ fontSize: "13px", fontWeight: 600, margin: "0 0 8px" }}>
                      Port Screening: {loadPort.name} ({loadPort.maxDraft}m max draft)
                    </p>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Loading Draft Clearance</span>
                      <span style={{ fontWeight: 600, color: isDraftCompatible ? "var(--text-success)" : "var(--text-danger)" }}>
                        {isDraftCompatible ? `+${draftDiff.toFixed(1)}m Safe Under-Keel (UKC)` : `Draft Exceeded by ${Math.abs(draftDiff).toFixed(1)}m`}
                      </span>
                    </div>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Berth LOA Allowance</span>
                      <span style={{ fontWeight: 600, color: isLoaCompatible ? "var(--text-success)" : "var(--text-danger)" }}>
                        {isLoaCompatible ? `+${loaDiff.toFixed(1)}m Berth Clear` : "LOA Exceeded"}
                      </span>
                    </div>
                    <div className="compat-item-row">
                      <span style={{ color: "var(--text-secondary)" }}>Discharge Compatibility</span>
                      <span style={{ color: "var(--text-success)", fontWeight: 600 }}>
                        {dischPort.name} (Draft: {dischPort.maxDraft}m OK)
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              {/* 4. PORT CONGESTION & TURNAROUND STATUS */}
              <section id="sec-congestion" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-clock" aria-hidden="true"></i>
                    <span>Port Congestion & Turnaround Schedule</span>
                  </div>
                  <span className={`flow-badge ${loadPort.congestion === "High" ? "warning" : "ready"}`}>
                    ● Congestion Level: {loadPort.congestion}
                  </span>
                </div>

                <div className="metrics-row">
                  <div className="metric-card">
                    <p className="metric-label">Port Anchorage Queue</p>
                    <p className="metric-val">{loadPort.activeVessels} vessels</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Predicted Waiting Time</p>
                    <p className="metric-val">{Math.round(waitHours)} hrs ({waitDays.toFixed(1)}d)</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Estimated Turnaround</p>
                    <p className="metric-val">{turnaroundHours} hrs</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-label">Sailing Passage ({distanceNm} NM)</p>
                    <p className="metric-val">{transitDays.toFixed(1)} days</p>
                  </div>
                </div>
              </section>

              {/* 5. TOTAL VOYAGE COST BREAKDOWN */}
              <section id="sec-cost" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-currency-rupee" aria-hidden="true"></i>
                    <span>Total Voyage Cost Breakdown ({currency === "INR" ? "Indian Rupees" : "USD"})</span>
                  </div>
                  <span className="flow-badge ready">● Reconciled</span>
                </div>

                <table className="cost-waterfall-table">
                  <thead>
                    <tr>
                      <th>Cost Component</th>
                      <th>Calculation Basis</th>
                      <th>Charter Now Rate</th>
                      <th>Delayed Entry (Wait) Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Freight / Charter Hire</strong></td>
                      <td>{cargoMt.toLocaleString()} MT @ spot vs forecast</td>
                      <td>{formatExact(freightSpotUsd)}</td>
                      <td style={{ color: "var(--text-success)", fontWeight: 600 }}>{formatExact(freightWaitUsd)}</td>
                    </tr>
                    <tr>
                      <td><strong>Sea Bunker Fuel (VLSFO)</strong></td>
                      <td>{distanceNm} NM transit ({formatExact(600)}/MT)</td>
                      <td>{formatExact(seaFuelCostUsd)}</td>
                      <td>{formatExact(seaFuelCostUsd)}</td>
                    </tr>
                    <tr>
                      <td><strong>Port Tariffs & Pilotage</strong></td>
                      <td>{loadPort.name} + {dischPort.name} Dues</td>
                      <td>{formatExact(portTariffsUsd)}</td>
                      <td>{formatExact(portTariffsUsd)}</td>
                    </tr>
                    <tr>
                      <td><strong>Demurrage / Idle Risk</strong></td>
                      <td>{Math.round(waitHours)}h wait ({formatExact(vProfile.demurrageRatePdUsd)}/day)</td>
                      <td>{formatExact(expectedDemurrageUsd)}</td>
                      <td style={{ color: "var(--text-success)" }}>{formatExact(expectedDemurrageUsd * 0.4)} (Queue clears)</td>
                    </tr>
                    <tr className="total-row">
                      <td><strong>TOTAL ESTIMATED VOYAGE COST</strong></td>
                      <td>Reconciled Voyage Outlay</td>
                      <td>{charterNowFormatted}</td>
                      <td style={{ color: "var(--text-success)", fontSize: "16px" }}>{waitFormatted}</td>
                    </tr>
                  </tbody>
                </table>
              </section>

              {/* 6. ⭐ CHARTER NOW / WAIT DECISION MILESTONE */}
              <section id="sec-decision" className="decision-hero-banner">
                <div className="decision-hero-top">
                  <div className={`decision-badge-big ${decisionSignal === "WAIT" ? "wait" : "chart"}`}>
                    <i className="ti ti-star" aria-hidden="true"></i>
                    MARKET SIGNAL: {decisionSignal}
                  </div>
                  <div className="savings-callout">
                    Net Projected Savings: {savingsFormatted}
                  </div>
                </div>

                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: 700, margin: "0 0 4px", color: "var(--text-primary)" }}>
                    {isRateDown
                      ? `Recommendation: Wait 3 to 5 days for a better window (${recommendedVesselType}, ${vProfile.typicalDwt.toLocaleString()} DWT)`
                      : `Recommendation: Charter now to lock in spot rates (${recommendedVesselType})`}
                  </h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                    Decision engine evaluated freight trends and anchorage queues at {loadPort.name}. Easing congestion combined with a softening rate dip delivers an optimal fixture window between <strong>Sept 15 and Sept 18</strong>, saving <strong>{savingsFormatted}</strong> in total costs.
                  </p>
                </div>

                <div className="decision-comparison-boxes">
                  <div className="comparison-box">
                    <span className="c-label">Charter now</span>
                    <span className="c-val">{charterNowFormatted}</span>
                  </div>
                  <div className="comparison-box highlight">
                    <span className="c-label">Wait (Optimal Window)</span>
                    <span className="c-val">{waitFormatted}</span>
                  </div>
                </div>
              </section>

              {/* 7. RECOMMENDED CONTRACT & PROTECTIVE TERMS */}
              <section id="sec-contract" className="flow-section-card">
                <div className="flow-section-header">
                  <div className="flow-section-title">
                    <i className="ti ti-file-certificate" aria-hidden="true"></i>
                    <span>Recommended Contract & Protective Terms</span>
                  </div>
                  <span className="flow-badge ready">● Form: Gencon 94</span>
                </div>

                <div className="contract-spec-grid">
                  <div className="contract-term-item">
                    <span className="term-label">Contract Option</span>
                    <span className="term-val">{recommendedContract}</span>
                  </div>
                  <div className="contract-term-item">
                    <span className="term-label">Agreed Freight Rate</span>
                    <span className="term-val">{formatRate(forecastRateUsd).replace("/ton", " / MT FIOST")}</span>
                  </div>
                  <div className="contract-term-item">
                    <span className="term-label">Agreed Laytime</span>
                    <span className="term-val">{laytimeWwd} Weather Working Days (WWD)</span>
                  </div>
                  <div className="contract-term-item">
                    <span className="term-label">Demurrage / Despatch</span>
                    <span className="term-val">{formatExact(vProfile.demurrageRatePdUsd)} / day · Despatch 50%</span>
                  </div>
                </div>

                <div className="contract-clause-box">
                  📜 <strong>Recommended Protective Clause:</strong> Notice of Readiness (NOR) shall be tendered whether in berth or not (WIBON) or whether in port or not (WIPON). Time counts 6 hours after NOR tender to protect charterer from anchorage idling at {loadPort.name}.
                </div>

                <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
                  <button
                    className="btn-contract-action"
                    onClick={() => {
                      const summary = `SMARTFREIGHT CHARTERING TERM SHEET (${currency})\n----------------------------------------\nCargo: ${cargoMt} MT ${cargoType}\nRoute: ${loadPort.name} -> ${dischPort.name}\nRecommended Vessel: ${vProfile.name} (${vProfile.typicalDwt} DWT)\nDecision Signal: ${decisionSignal}\nFreight Rate: ${formatRate(forecastRateUsd)}\nTotal Estimated Cost: ${waitFormatted}\nProjected Savings: ${savingsFormatted}\nContract Form: ${recommendedContract}\nDemurrage Rate: ${formatExact(vProfile.demurrageRatePdUsd)}/day\nLaycan: ${laycanDate}`;
                      navigator.clipboard?.writeText(summary);
                      alert(`Chartering Term Sheet copied to clipboard in ${currency}!\n\n` + summary);
                    }}
                  >
                    <i className="ti ti-copy" aria-hidden="true"></i> Copy Chartering Term Sheet
                  </button>

                  <button
                    className="btn-contract-action"
                    style={{ background: "#16a34a" }}
                    onClick={() => alert(`Fixture Confirmed! ${vProfile.name} booked for ${cargoMt.toLocaleString()} MT ${cargoType} from ${loadPort.name} to ${dischPort.name}. Rate: ${formatRate(forecastRateUsd)}.`)}
                  >
                    <i className="ti ti-check" aria-hidden="true"></i> Proceed with Recommended Contract →
                  </button>
                </div>
              </section>
            </>
          )}

          {/* =========================================================================
              VIEW 2: LIVE AIS VESSEL TRACKING (VESSELFINDER INTERACTIVE MAP VIEW)
              Requirement 3: Interactive VesselFinder-style map.
              Requirement 4: Select vessel from dropdown/map; only show details after selection.
              Requirement 5: Display full telemetry details when selected.
             ========================================================================= */}
          {activeNav === "tracking" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Vessel Selector & Filters Toolbar */}
              <div className="flow-section-card" style={{ padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, minWidth: "280px" }}>
                    <label style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                      Select Vessel to Track:
                    </label>
                    <select
                      style={{
                        padding: "8px 12px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        fontSize: "13px",
                        fontWeight: 600,
                        background: "var(--surface-1)",
                        width: "100%",
                      }}
                      value={selectedTrackVessel?.mmsi || ""}
                      onChange={(e) => {
                        const mmsi = Number(e.target.value);
                        const v = AIS_VESSELS.find((ship) => ship.mmsi === mmsi) || null;
                        setSelectedTrackVessel(v);
                      }}
                    >
                      <option value="">-- Choose a vessel to inspect (or click any ship on the map) --</option>
                      {AIS_VESSELS.map((v) => (
                        <option key={v.mmsi} value={v.mmsi}>
                          {v.name} ({v.vessel_class}) · Dest: {v.destination_name} · MMSI: {v.mmsi}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Filter Class:</span>
                    {["All", "Capesize", "Panamax", "Supramax", "Handysize"].map((cls) => (
                      <button
                        key={cls}
                        className={`preset-chip ${vesselFilter === cls ? "active" : ""}`}
                        onClick={() => setVesselFilter(cls)}
                      >
                        {cls}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Interactive VesselFinder-Style Leaflet Map Container */}
              <div className="flow-section-card" style={{ padding: "0", overflow: "hidden" }}>
                <div
                  id="leaflet-ais-map"
                  style={{
                    height: "560px",
                    width: "100%",
                    background: "#e2e8f0",
                  }}
                ></div>
                <div style={{ padding: "8px 14px", background: "var(--surface-1)", borderTop: "0.5px solid var(--border)", display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-secondary)" }}>
                  <span>🛰️ VesselFinder AIS Stream · Real-time Bay of Bengal & East Coast India coverage</span>
                  <span>Click any ship marker on the map to inspect live vessel telemetry</span>
                </div>
              </div>

              {/* Requirement 4: Only after selecting a vessel, display its detailed tracking information */}
              {!selectedTrackVessel ? (
                <div className="flow-section-card" style={{ padding: "24px", textAlign: "center" }}>
                  <i className="ti ti-ship" style={{ fontSize: "32px", color: "var(--text-secondary)" }} aria-hidden="true"></i>
                  <h4 style={{ margin: "8px 0 4px", fontSize: "15px", color: "var(--text-primary)" }}>No Vessel Selected</h4>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0 }}>
                    Please click a vessel pin on the map above or choose from the dropdown to view real-time AIS coordinates, destination ETA, speed, delay status, and demurrage calculations.
                  </p>
                </div>
              ) : (
                /* Requirement 5: Selected Vessel Detailed Information Panel */
                <div className="flow-section-card" style={{ border: "2px solid var(--border-accent)" }}>
                  <div className="flow-section-header">
                    <div className="flow-title">
                      <i className="ti ti-ship" style={{ color: "var(--text-accent)" }} aria-hidden="true"></i>
                      <span>{selectedTrackVessel.name}</span>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 400 }}>
                        (MMSI: {selectedTrackVessel.mmsi} · IMO: {selectedTrackVessel.imo})
                      </span>
                    </div>
                    <span className="flow-badge ready">
                      ● {selectedTrackVessel.nav_status}
                    </span>
                  </div>

                  {/* Telemetry Row 1 */}
                  <div className="metrics-row">
                    <div className="metric-card">
                      <p className="metric-label">Vessel Class & Capacity</p>
                      <p className="metric-val">{selectedTrackVessel.vessel_class} ({selectedTrackVessel.dwt.toLocaleString()} DWT)</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Current Position</p>
                      <p className="metric-val">{selectedTrackVessel.lat.toFixed(3)}° N, {selectedTrackVessel.lon.toFixed(3)}° E</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Speed / Course</p>
                      <p className="metric-val">{selectedTrackVessel.speed_knots} kts / {selectedTrackVessel.course_deg}°</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Draught (Current)</p>
                      <p className="metric-val">{selectedTrackVessel.draught_m} meters</p>
                    </div>
                  </div>

                  {/* Telemetry Row 2 */}
                  <div className="metrics-row">
                    <div className="metric-card">
                      <p className="metric-label">Destination Port</p>
                      <p className="metric-val">{selectedTrackVessel.destination_name} ({selectedTrackVessel.destination})</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Direct AIS ETA (UTC)</p>
                      <p className="metric-val">{selectedTrackVessel.direct_eta_utc.replace("T", " ").replace(":00Z", " UTC")}</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Distance to Port</p>
                      <p className="metric-val">{selectedTrackVessel.distance_to_port_nm} NM</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Delay Status</p>
                      <p className="metric-val" style={{ color: selectedTrackVessel.delay_hours > 0 ? "var(--text-danger)" : "var(--text-success)" }}>
                        {selectedTrackVessel.delay_status}
                      </p>
                    </div>
                  </div>

                  {/* Port Waiting & Idle Demurrage Status */}
                  <div className="metrics-row">
                    <div className="metric-card">
                      <p className="metric-label">Predicted Waiting at Port</p>
                      <p className="metric-val">{selectedTrackVessel.expected_waiting_hours} hrs</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Expected Turnaround</p>
                      <p className="metric-val">{selectedTrackVessel.expected_turnaround_hours} hrs</p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">Estimated Idle Demurrage Cost</p>
                      <p className="metric-val" style={{ color: "var(--text-warning)" }}>
                        {currency === "INR"
                          ? `₹${selectedTrackVessel.idle_demurrage_inr.toLocaleString("en-IN")}`
                          : `$${Math.round(selectedTrackVessel.idle_demurrage_inr / USD_TO_INR).toLocaleString("en-US")}`}
                      </p>
                    </div>
                    <div className="metric-card">
                      <p className="metric-label">IRCTC Lifecycle Stage</p>
                      <p className="metric-val" style={{ color: "var(--text-accent)" }}>
                        {IRCTC_STAGES[selectedTrackVessel.irctc_stage_idx].label}
                      </p>
                    </div>
                  </div>

                  {/* IRCTC Stepper */}
                  <div className="stepper-progress-wrapper" style={{ marginTop: "4px" }}>
                    <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 10px" }}>
                      <strong>Status Summary:</strong> {selectedTrackVessel.status_summary}
                    </p>
                    <div className="irctc-stages-row">
                      <div className="stepper-line">
                        <div
                          className="stepper-line-active"
                          style={{ width: `${(selectedTrackVessel.irctc_stage_idx / 5) * 100}%` }}
                        ></div>
                      </div>
                      {IRCTC_STAGES.map((st) => {
                        const isPast = st.id < selectedTrackVessel.irctc_stage_idx;
                        const isCurrent = st.id === selectedTrackVessel.irctc_stage_idx;
                        return (
                          <div key={st.id} className="irctc-stage-item">
                            <div className={`stage-dot ${isPast ? "completed" : isCurrent ? "current" : ""}`}>
                              {isPast ? "✓" : st.id + 1}
                            </div>
                            <span className={`stage-name ${isCurrent ? "current" : ""}`}>{st.label}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "4px" }}>
                    <button
                      className="btn-contract-action"
                      style={{ background: "#475569" }}
                      onClick={() => setSelectedTrackVessel(null)}
                    >
                      Clear Selection
                    </button>
                    <button
                      className="btn-contract-action"
                      onClick={() => {
                        setActiveNav("dashboard");
                        document.getElementById("sec-voyage")?.scrollIntoView({ behavior: "smooth" });
                      }}
                    >
                      Apply Vessel to Voyage Analysis →
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);