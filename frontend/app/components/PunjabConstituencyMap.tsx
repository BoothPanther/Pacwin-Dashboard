"use client";

import { useEffect, useMemo, useState } from "react";
import {
  GeoJSON,
  MapContainer,
  useMap,
} from "react-leaflet";

import type { Layer, PathOptions } from "leaflet";
import type {
  Feature,
  FeatureCollection,
  Geometry,
} from "geojson";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

/* ============================================================
   TYPES
   ============================================================ */

type Seat = {
  id: number;
  assembly_number: number;
  name: string;
  code: string;
  category: string;
  district: string;
};

type ACProperties = {
  st_code?: string;
  st_name?: string;
  dist_name?: string;
  ac_no?: number | string;
  ac_name?: string;
  AC_ID?: string;
};

type ACFeature = Feature<
  Geometry,
  ACProperties
>;

type ACFeatureCollection = FeatureCollection<
  Geometry,
  ACProperties
>;

type Props = {
  seats: Seat[];
  selectedSeatId: number | null;
  onSeatSelect: (seatId: number) => void;
};

/* ============================================================
   VALIDATE ASSEMBLY CONSTITUENCY FEATURE
   ============================================================ */

function isValidACFeature(
  feature: ACFeature
): boolean {
  const rawACNumber =
    feature.properties?.ac_no;

  const acNumber = Number(rawACNumber);

  return (
    Number.isInteger(acNumber) &&
    acNumber >= 1 &&
    acNumber <= 117
  );
}

/* ============================================================
   MAP VIEW CONTROLLER
   ============================================================ */

function MapViewController({
  geoData,
  seats,
  selectedSeatId,
}: {
  geoData: ACFeatureCollection | null;
  seats: Seat[];
  selectedSeatId: number | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (
      !geoData ||
      geoData.features.length === 0
    ) {
      return;
    }

    const validFeatures =
      geoData.features.filter(
        (feature) =>
          isValidACFeature(
            feature as ACFeature
          )
      );

    if (validFeatures.length === 0) {
      return;
    }

    const timer =
      window.setTimeout(() => {
        map.invalidateSize(false);

        /* ==================================================
           SELECTED CONSTITUENCY
           ================================================== */

        if (selectedSeatId !== null) {
          const selectedSeat =
            seats.find(
              (seat) =>
                seat.id === selectedSeatId
            );

          if (selectedSeat) {
            const selectedFeature =
              validFeatures.find(
                (feature) =>
                  Number(
                    feature.properties?.ac_no
                  ) ===
                  selectedSeat.assembly_number
              );

            if (selectedFeature) {
              const selectedLayer =
                L.geoJSON(
                  selectedFeature
                );

              const bounds =
                selectedLayer.getBounds();

              if (bounds.isValid()) {
                map.fitBounds(
                  bounds,
                  {
                    paddingTopLeft: [
                      45,
                      45,
                    ],
                    paddingBottomRight: [
                      45,
                      45,
                    ],
                    maxZoom: 10,
                    animate: false,
                  }
                );

                return;
              }
            }
          }
        }

        /* ==================================================
           COMPLETE PUNJAB MAP
           ================================================== */

        const validGeoJSON: ACFeatureCollection =
          {
            type: "FeatureCollection",
            features:
              validFeatures as ACFeature[],
          };

        const fullLayer =
          L.geoJSON(
            validGeoJSON
          );

        const bounds =
          fullLayer.getBounds();

        if (bounds.isValid()) {
          map.fitBounds(
            bounds,
            {
              paddingTopLeft: [
                18,
                18,
              ],
              paddingBottomRight: [
                18,
                18,
              ],
              maxZoom: 8,
              animate: false,
            }
          );
        }
      }, 100);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    geoData,
    seats,
    selectedSeatId,
    map,
  ]);

  return null;
}

/* ============================================================
   MAIN MAP
   ============================================================ */

export default function PunjabConstituencyMap({
  seats,
  selectedSeatId,
  onSeatSelect,
}: Props) {
  const [geoData, setGeoData] =
    useState<ACFeatureCollection | null>(
      null
    );

  const [mapError, setMapError] =
    useState("");

  /* ==========================================================
     LOAD GEOJSON
     ========================================================== */

  useEffect(() => {
    let cancelled = false;

    async function loadGeoJSON() {
      try {
        setMapError("");

        const response =
          await fetch(
            "/data/punjab-ac.geojson"
          );

        if (!response.ok) {
          throw new Error(
            `GeoJSON request failed: ${response.status}`
          );
        }

        const data =
          (await response.json()) as ACFeatureCollection;

        if (
          !data.features ||
          !Array.isArray(
            data.features
          )
        ) {
          throw new Error(
            "Invalid Punjab constituency GeoJSON."
          );
        }

        /* ==================================================
           KEEP ONLY REAL ASSEMBLY CONSTITUENCIES
           ================================================== */

        const validFeatures =
          data.features.filter(
            (feature) =>
              isValidACFeature(
                feature as ACFeature
              )
          );

        if (
          validFeatures.length === 0
        ) {
          throw new Error(
            "No valid Assembly Constituency features found."
          );
        }

        if (!cancelled) {
          setGeoData({
            type: "FeatureCollection",
            features:
              validFeatures as ACFeature[],
          });
        }
      } catch (error) {
        console.error(
          "Punjab map loading error:",
          error
        );

        if (!cancelled) {
          setMapError(
            "Unable to load Punjab constituency map."
          );
        }
      }
    }

    loadGeoJSON();

    return () => {
      cancelled = true;
    };
  }, []);

  /* ==========================================================
     SEAT LOOKUP
     ========================================================== */

  const seatByAssemblyNumber =
    useMemo(() => {
      const lookup =
        new Map<number, Seat>();

      for (const seat of seats) {
        lookup.set(
          seat.assembly_number,
          seat
        );
      }

      return lookup;
    }, [seats]);

  /* ==========================================================
     STYLE
     ========================================================== */

  const getStyle = (
    feature?: ACFeature
  ): PathOptions => {
    const assemblyNumber =
      Number(
        feature?.properties?.ac_no
      );

    const seat =
      seatByAssemblyNumber.get(
        assemblyNumber
      );

    const isSelected =
      seat?.id === selectedSeatId;

    return {
      color: isSelected
        ? "#2563eb"
        : "#94a3b8",

      weight: isSelected
        ? 2.5
        : 0.8,

      opacity: 1,

      fillColor: isSelected
        ? "#bfdbfe"
        : "#f8fafc",

      fillOpacity: isSelected
        ? 0.9
        : 1,
    };
  };

  /* ==========================================================
     FEATURE EVENTS
     ========================================================== */

  const onEachFeature = (
    feature: ACFeature,
    layer: Layer
  ) => {
    const assemblyNumber =
      Number(
        feature.properties?.ac_no
      );

    const seat =
      seatByAssemblyNumber.get(
        assemblyNumber
      );

    const acName =
      feature.properties?.ac_name ||
      seat?.name ||
      "Assembly Constituency";

    const district =
      feature.properties?.dist_name ||
      seat?.district ||
      "";

    /* ======================================================
       TOOLTIP
       ====================================================== */

    layer.bindTooltip(
      `
        <div style="
          font-size:12px;
          line-height:1.5;
        ">
          <strong>
            AC ${String(
              assemblyNumber
            ).padStart(
              3,
              "0"
            )} — ${acName}
          </strong>

          ${
            district
              ? `<br/><span>${district}</span>`
              : ""
          }
        </div>
      `,
      {
        sticky: true,
        direction: "top",
        opacity: 0.95,
      }
    );

    /* ======================================================
       MOUSE EVENTS
       ====================================================== */

    layer.on({
      mouseover: (event) => {
        const target =
          event.target;

        target.setStyle({
          weight: 2,
          color: "#2563eb",

          fillColor:
            seat?.id ===
            selectedSeatId
              ? "#93c5fd"
              : "#e2e8f0",

          fillOpacity: 1,
        });

        target.bringToFront();
      },

      mouseout: (event) => {
        const target =
          event.target;

        target.setStyle(
          getStyle(feature)
        );
      },

      click: () => {
        if (seat) {
          onSeatSelect(
            seat.id
          );
        }
      },
    });
  };

  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <div className="relative h-[520px] w-full overflow-hidden bg-white">

      {mapError ? (
        <div className="flex h-full items-center justify-center text-sm text-red-500">
          {mapError}
        </div>
      ) : (
        <>

          <MapContainer
            center={[
              30.9,
              75.8,
            ]}
            zoom={7}
            minZoom={6}
            maxZoom={11}

            scrollWheelZoom={true}

            wheelDebounceTime={150}

            wheelPxPerZoomLevel={220}

            zoomDelta={0.5}

            zoomSnap={0.5}

            zoomControl={true}

            attributionControl={
              false
            }

            className="h-full w-full"

            style={{
              background:
                "#ffffff",
            }}
          >

            {geoData && (
              <>
                <MapViewController
                  geoData={
                    geoData
                  }
                  seats={seats}
                  selectedSeatId={
                    selectedSeatId
                  }
                />

                <GeoJSON
                  data={geoData}
                  style={getStyle}
                  onEachFeature={
                    onEachFeature
                  }
                />
              </>
            )}

          </MapContainer>

          {!geoData && (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="rounded-lg bg-white/90 px-4 py-3 text-sm text-slate-500 shadow-sm">
                Loading Punjab constituency map...
              </div>
            </div>
          )}

          {geoData && (
            <div className="pointer-events-none absolute bottom-3 left-3 z-[1000] rounded-md border border-slate-200 bg-white/90 px-3 py-1.5 text-[11px] text-slate-500 shadow-sm">
              {
                geoData
                  .features
                  .length
              }{" "}
              Assembly Constituencies
            </div>
          )}

        </>
      )}

    </div>
  );
}