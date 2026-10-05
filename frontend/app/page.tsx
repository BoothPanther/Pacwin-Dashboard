"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

const PunjabConstituencyMap = dynamic(
  () => import("./components/PunjabConstituencyMap"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[520px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500">
        Loading Punjab constituency map...
      </div>
    ),
  }
);

/* =========================================================
   TYPES
   ========================================================= */

type Seat = {
  id: number;
  assembly_number: number;
  name: string;
  code: string;
  category: string;
  district: string;
};

type SeatReport = {
  id: number;
  report_name: string;
  original_file_name: string;
  file_format: string;
  processing_status: string;
  report_date: string | null;
};

type ReportSummary = {
  summary: string | null;
  total_voters: number | null;
  male_percentage: number | null;
  female_percentage: number | null;
  rural_percentage: number | null;
  urban_percentage: number | null;
  religious_composition: string | null;
};

type ElectionResult = {
  id: number;
  election_year: number;
  election_type: string | null;
  party_name: string | null;
  candidate_name: string | null;
  votes: number | null;
  vote_percentage: number | null;
  source_note: string | null;
};

type PartyAnalysis = {
  id: number;
  party_name: string;
  analysis: string | null;
};

type CandidateAnalysis = {
  id: number;
  candidate_name: string;
  party_name: string | null;
  analysis: string | null;
};

type AreaAnalysis = {
  id: number;
  area_name: string;
  analysis: string | null;
};

type ReportIssue = {
  id: number;
  issue_title: string;
  issue_description: string | null;
};

type FullSeatReport = {
  status?: string;
  seat?: Seat;
  report: SeatReport | null;
  summary: ReportSummary | null;
  election_results: ElectionResult[];
  party_analysis: PartyAnalysis[];
  candidate_analysis: CandidateAnalysis[];
  area_analysis: AreaAnalysis[];
  issues: ReportIssue[];
};

/* =========================================================
   BOOTH-WISE ANALYSIS TYPE
   ========================================================= */

type Booth = {
  id: number;
  booth_number: string;
  booth_name: string | null;
  polling_station: string | null;
  area: string | null;
  winner_by_year: Record<string, string>;
};
/* =========================================================
   MAIN PAGE
   ========================================================= */

export default function Home() {
  const [seats, setSeats] = useState<Seat[]>([]);
  const [selectedSeatId, setSelectedSeatId] = useState<number | null>(null);

  const handleSeatSelect = (value: number | null) => {
  if (value === null) {
    setSelectedSeatId(null);
    return;
  }

  // First: value is already the database ID
  const seatById = seats.find((seat) => seat.id === value);

  if (seatById) {
    setSelectedSeatId(seatById.id);
    return;
  }

  // Second: value may be the AC / Assembly Number
  const seatByAssemblyNumber = seats.find(
    (seat) => seat.assembly_number === value
  );

  if (seatByAssemblyNumber) {
    setSelectedSeatId(seatByAssemblyNumber.id);
    return;
  }

  console.error("Unable to resolve constituency:", value);
};

  const [seatsLoading, setSeatsLoading] = useState(true);
  const [seatError, setSeatError] = useState("");

  const [seatReport, setSeatReport] =
    useState<FullSeatReport | null>(null);

  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");

  /* =======================================================
     BOOTH-WISE ANALYSIS STATE
     ======================================================= */

  const [booths, setBooths] = useState<Booth[]>([]);
  const [boothsLoading, setBoothsLoading] = useState(false);
  const [boothsError, setBoothsError] = useState("");

  const boothYears = useMemo(() => {
    const years = new Set<number>();

    booths.forEach((booth) => {
      Object.keys(booth.winner_by_year || {}).forEach((year) => {
        const parsedYear = Number(year);

        if (Number.isFinite(parsedYear)) {
          years.add(parsedYear);
        }
      });
    });

    return Array.from(years).sort((a, b) => a - b);
  }, [booths]);

  /* =======================================================
   BOOTH WINNER PARTY COLORS
   ======================================================= */

const getWinnerPartyClass = (party: string | null) => {
  switch (party) {
    case "INC":
      return "text-green-400";

    case "AAP":
    case "APP":
      return "text-blue-400";

    case "SAD":
      return "text-yellow-400";

    case "BJP":
      return "text-orange-400";

    case "BSP":
      return "text- dark purple-400";

    default:
      return "text-slate-500";
  }
};
const getWinnerForYear = (booth: Booth, year: number): string | null => {
  return booth.winner_by_year?.[String(year)] ?? null;
};

  /* =======================================================
     LOAD ALL 117 SEATS
     ======================================================= */

  useEffect(() => {
    let cancelled = false;

    async function loadSeats() {
      try {
        setSeatsLoading(true);
        setSeatError("");

        const response = await fetch(
          "http://127.0.0.1:8000/api/seats"
        );

        if (!response.ok) {
          throw new Error("Failed to load seats");
        }

        const data = await response.json();

        if (!data.seats || !Array.isArray(data.seats)) {
          throw new Error("Invalid seat data received from API");
        }

        if (cancelled) {
          return;
        }

        setSeats(data.seats);

        if (data.seats.length > 0) {
          setSelectedSeatId((currentId: number | null) => {
            if (
              currentId !== null &&
              data.seats.some(
                (seat: Seat) => seat.id === currentId
              )
            ) {
              return currentId;
            }

            return data.seats[0].id;
          });
        }
      } catch (error) {
        console.error("Seat loading error:", error);

        if (!cancelled) {
          setSeatError(
            "Unable to load seats from the Pacwin server."
          );
        }
      } finally {
        if (!cancelled) {
          setSeatsLoading(false);
        }
      }
    }

    loadSeats();

    return () => {
      cancelled = true;
    };
  }, []);

  /* =======================================================
     LOAD SELECTED SEAT REPORT
     ======================================================= */

  useEffect(() => {
    let cancelled = false;

    async function loadSeatReport() {
      if (selectedSeatId === null) {
        setSeatReport(null);
        setReportError("");
        return;
      }

      try {
        setReportLoading(true);
        setReportError("");
        setSeatReport(null);

        const response = await fetch(
          `http://127.0.0.1:8000/api/seats/${selectedSeatId}/report`
        );

        if (!response.ok) {
          throw new Error(
            `Report API returned ${response.status}`
          );
        }

        const data = await response.json();

        if (cancelled) {
          return;
        }

        if (data.status !== "success") {
          throw new Error("Invalid report response");
        }

        setSeatReport({
          status: data.status,
          seat: data.seat ?? undefined,
          report: data.report ?? null,
          summary: data.summary ?? null,
          election_results: Array.isArray(
            data.election_results
          )
            ? data.election_results
            : [],
          party_analysis: Array.isArray(data.party_analysis)
            ? data.party_analysis
            : [],
          candidate_analysis: Array.isArray(
            data.candidate_analysis
          )
            ? data.candidate_analysis
            : [],
          area_analysis: Array.isArray(data.area_analysis)
            ? data.area_analysis
            : [],
          issues: Array.isArray(data.issues)
            ? data.issues
            : [],
        });
      } catch (error) {
        console.error("Report loading error:", error);

        if (!cancelled) {
          setSeatReport(null);
          setReportError(
            "Unable to load report information for this constituency."
          );
        }
      } finally {
        if (!cancelled) {
          setReportLoading(false);
        }
      }
    }

    loadSeatReport();

    return () => {
      cancelled = true;
    };
  }, [selectedSeatId]);

   /* =======================================================
     LOAD BOOTH-WISE ANALYSIS
     ======================================================= */

  useEffect(() => {
    let cancelled = false;

    async function loadBooths() {
      if (selectedSeatId === null) {
        setBooths([]);
        setBoothsError("");
        return;
      }

      try {
        setBoothsLoading(true);
        setBoothsError("");
        setBooths([]);

        const response = await fetch(
          `http://127.0.0.1:8000/api/booths/constituency/${selectedSeatId}`
        );

        /*
         * 404 means the selected constituency does not have
         * booth-wise data uploaded yet.
         *
         * This is NOT treated as a system/API error.
         */
        if (response.status === 404) {
          if (!cancelled) {
            setBooths([]);
            setBoothsError("");
          }

          return;
        }

        /*
         * Any other non-success response is a real API error.
         */
        if (!response.ok) {
          throw new Error(
            `Booth API returned ${response.status}`
          );
        }

        const data = await response.json();

        if (cancelled) {
          return;
        }

        if (
          data.status !== "success" ||
          !Array.isArray(data.booths)
        ) {
          throw new Error("Invalid booth response");
        }

        setBooths(
          data.booths.map((booth: Booth) => ({
            ...booth,
            winner_by_year: booth.winner_by_year || {},
          }))
        );
      } catch (error) {
        console.error("Booth loading error:", error);

        if (!cancelled) {
          setBooths([]);
          setBoothsError(
            "Unable to load booth-wise analysis for this constituency."
          );
        }
      } finally {
        if (!cancelled) {
          setBoothsLoading(false);
        }
      }
    }

    loadBooths();

    return () => {
      cancelled = true;
    };
  }, [selectedSeatId]);

  /* =======================================================
     SELECTED SEAT
     ======================================================= */

  const selectedSeat =
    seats.find((seat) => seat.id === selectedSeatId) ?? null;

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <main className="min-h-screen bg-[#07111f] text-white">

      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="border-b border-white/10 bg-[#091525]">
        <div className="flex h-20 items-center justify-between px-6 lg:px-8">

          <div className="flex items-center gap-4">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-sm font-black text-[#07111f]">
              P
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-wide">
                PACWIN
              </h1>

              <p className="text-xs text-slate-400">
                Political Intelligence Platform
              </p>
            </div>

          </div>

          <div className="text-right">
            <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
              State Dashboard
            </p>

            <h2 className="text-xl font-semibold">
              Punjab Election Dashboard
            </h2>
          </div>

        </div>
      </header>

      {/* =====================================================
          MAIN CONTENT
          ===================================================== */}

      <div className="p-6 lg:p-8">

        {/* ===================================================
            CONTROL BAR
            =================================================== */}

        <section className="mb-6 rounded-2xl border border-white/10 bg-[#0c192b] p-5 shadow-2xl shadow-black/10">

          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">

            <div>
              <p className="mb-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                Punjab State
              </p>

              <h2 className="text-2xl font-semibold">
                Constituency Intelligence
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Select a seat to view constituency intelligence.
              </p>
            </div>

            <div className="w-full lg:w-[360px]">

              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-slate-400">
                Select Constituency / Seat
              </label>

              <select
                value={selectedSeatId ?? ""}
                onChange={(event) => {
                  const value = event.target.value;

                  if (value === "") {
                    setSelectedSeatId(null);
                    return;
                  }

                  handleSeatSelect(Number(value));
                }}
                disabled={seatsLoading}
                className="w-full rounded-xl border border-white/10 bg-[#111f32] px-4 py-3 text-sm text-white outline-none transition focus:border-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {seatsLoading ? (
                  <option value="">
                    Loading seats...
                  </option>
                ) : seats.length === 0 ? (
                  <option value="">
                    No seats available
                  </option>
                ) : (
                  seats.map((seat) => (
                    <option
                      key={seat.id}
                      value={seat.id}
                      className="bg-[#111f32]"
                    >
                      AC{" "}
                      {String(
                        seat.assembly_number
                      ).padStart(3, "0")}{" "}
                      — {seat.name}
                    </option>
                  ))
                )}
              </select>

              {seatError && (
                <p className="mt-2 text-xs text-red-400">
                  {seatError}
                </p>
              )}

              {!seatsLoading && seats.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">
                  {seats.length} seats loaded from Pacwin database
                </p>
              )}

            </div>

          </div>

        </section>

        {/* ===================================================
            MAP + SEAT SUMMARY
            =================================================== */}

        <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">

          {/* =================================================
              MAP
              ================================================= */}

          <div className="relative self-start overflow-hidden rounded-2xl border border-white/10 bg-white">

            <div className="absolute left-6 top-6 z-[1000]">

              <div className="rounded-xl border border-slate-200 bg-white/95 px-4 py-3 shadow-sm">

                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                  Geographic View
                </p>

                <h3 className="mt-1 text-xl font-semibold text-slate-900">
                  Punjab State Map
                </h3>

              </div>

            </div>
<PunjabConstituencyMap
  seats={seats}
  selectedSeatId={selectedSeatId}
  onSeatSelect={handleSeatSelect}
/>

            <div className="border-t border-slate-200 bg-white px-6 py-4">

              <div className="flex flex-wrap items-center gap-5 text-xs text-slate-500">

                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm border-2 border-blue-600 bg-blue-200" />

                  <span>
                    Selected seat
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm border border-slate-400 bg-slate-50" />

                  <span>
                    Assembly Constituency
                  </span>
                </div>

                <div className="ml-auto text-slate-400">
                  Click any constituency
                </div>

              </div>

            </div>

          </div>

          {/* =================================================
              SELECTED SEAT / REPORT SUMMARY
              ================================================= */}

          <div className="flex h-full flex-col">

            <section className="flex h-full flex-col rounded-2xl border border-white/10 bg-[#0c192b] p-6">

              <div className="mb-6">

                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                  Constituency Intelligence
                </p>

                <h3 className="mt-1 text-2xl font-semibold">
                  {selectedSeat
                    ? `AC ${String(
                        selectedSeat.assembly_number
                      ).padStart(3, "0")} — ${
                        selectedSeat.name
                      }`
                    : "Select a Seat"}
                </h3>

                {selectedSeat && (
                  <p className="mt-1 text-sm text-slate-400">
                    {selectedSeat.district} •{" "}
                    {selectedSeat.code}
                  </p>
                )}

              </div>

              {/* =================================================
                  REPORT SUMMARY
                  ================================================= */}

              <div className="mt-6 flex flex-1 flex-col rounded-xl border border-white/10 bg-[#101f33] p-6">

                <div className="flex items-start justify-between gap-4">

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Report Summary
                    </p>

                    <h4 className="mt-2 text-lg font-semibold text-white">
                      {selectedSeat
                        ? `${selectedSeat.name} Constituency Report`
                        : "No Constituency Selected"}
                    </h4>
                  </div>

                  {seatReport?.report && (
                    <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[10px] uppercase tracking-wider text-emerald-400">
                      Report Available
                    </span>
                  )}

                </div>

                <div className="mt-6 flex flex-1 flex-col rounded-lg border border-white/5 bg-[#0c192b] p-6">

                  {!selectedSeat ? (
                    <p className="text-sm text-slate-500">
                      Select an Assembly Constituency from the
                      map or dropdown to view its report.
                    </p>
                  ) : reportLoading ? (
                    <p className="text-sm text-slate-400">
                      Loading constituency report...
                    </p>
                  ) : reportError ? (
                    <p className="text-sm text-red-400">
                      {reportError}
                    </p>
                  ) : seatReport?.report ? (
                    <>
                      <p className="text-[17px] leading-8 text-slate-200">
                        {seatReport.summary?.summary ||
                          "Report uploaded, but no summary is available yet."}
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-slate-500">
                      No constituency report has been uploaded
                      for this seat yet.
                    </p>
                  )}

                </div>

              </div>

            </section>

          </div>

        </section>

        {/* =====================================================
            REPORT DATA
            ===================================================== */}

        {reportLoading && (
          <section className="mt-6 rounded-2xl border border-white/10 bg-[#0c192b] p-6">
            <p className="text-sm text-slate-400">
              Loading constituency report data...
            </p>
          </section>
        )}

        {reportError && (
          <section className="mt-6 rounded-2xl border border-red-400/20 bg-red-400/5 p-6">
            <p className="text-sm text-red-300">
              {reportError}
            </p>
          </section>
        )}

        {!reportLoading &&
          !reportError &&
          selectedSeat && (
            <>
              {/* =================================================
                  DEMOGRAPHIC SUMMARY
                  ================================================= */}

              {seatReport?.summary && (
                <section className="mt-6 rounded-2xl border border-white/10 bg-[#0c192b] p-6">

                  <div className="mb-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                      Constituency Profile
                    </p>

                    <h3 className="mt-1 text-xl font-semibold">
                      Demographic Data
                    </h3>

                    <p className="mt-1 text-xs text-slate-500">
                      Voter composition reproduced from the uploaded constituency report.
                    </p>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">

                    <StatCard
                      title="Total Voters"
                      value={
                        seatReport.summary.total_voters != null
                          ? seatReport.summary.total_voters.toLocaleString(
                              "en-IN"
                            )
                          : "—"
                      }
                      subtitle="Report data"
                    />

                    <StatCard
                      title="Male"
                      value={
                        seatReport.summary.male_percentage != null
                          ? `${seatReport.summary.male_percentage}%`
                          : "—"
                      }
                      subtitle="Report data"
                    />

                    <StatCard
                      title="Female"
                      value={
                        seatReport.summary.female_percentage != null
                          ? `${seatReport.summary.female_percentage}%`
                          : "—"
                      }
                      subtitle="Report data"
                    />

                    <StatCard
                      title="Rural"
                      value={
                        seatReport.summary.rural_percentage != null
                          ? `${seatReport.summary.rural_percentage}%`
                          : "—"
                      }
                      subtitle="Report data"
                    />

                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">

                    <div className="rounded-xl border border-white/5 bg-[#101f33] p-4">
                      <p className="text-xs uppercase tracking-wider text-slate-500">
                        Urban
                      </p>

                      <p className="mt-3 text-2xl font-bold text-white">
                        {seatReport.summary.urban_percentage != null
                          ? `${seatReport.summary.urban_percentage}%`
                          : "—"}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Report data
                      </p>
                    </div>

                    <div className="rounded-xl border border-white/5 bg-[#101f33] p-4">
                      <p className="text-xs uppercase tracking-wider text-slate-500">
                        Religious Composition
                      </p>

                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        {seatReport.summary
                          .religious_composition || "—"}
                      </p>
                    </div>

                  </div>

                </section>
              )}

              {/* =================================================
                  BOOTH-WISE ANALYSIS
                  ================================================= */}

              <section className="mt-6 rounded-2xl border border-white/10 bg-[#0c192b] p-6">

                <div className="mb-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                    Constituency Operations
                  </p>

                  <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">

                    <div>
                      <h3 className="mt-1 text-xl font-semibold">
                        Booth-wise Analysis
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        Booth-level winner party data from the available source records.
                      </p>
                    </div>

                    {!boothsLoading && booths.length > 0 && (
                      <p className="text-xs text-slate-500">
                        {booths.length} booths
                      </p>
                    )}

                  </div>
                </div>

                {boothsLoading ? (
                  <div className="rounded-xl border border-white/5 bg-[#101f33] p-6">
                    <p className="text-sm text-slate-400">
                      Loading booth-wise analysis...
                    </p>
                  </div>
                ) : boothsError ? (
                  <div className="rounded-xl border border-red-400/20 bg-red-400/5 p-6">
                    <p className="text-sm text-red-300">
                      {boothsError}
                    </p>
                  </div>
                ) : booths.length === 0 ? (
                  <div className="rounded-xl border border-white/5 bg-[#101f33] p-6">
                    <p className="text-sm text-slate-500">
                      No booth-wise data is available for this constituency.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-xl border border-white/10">

                    <div className="max-h-[650px] overflow-auto">

                      <table className="min-w-[900px] w-full border-collapse text-left">

                        <thead className="sticky top-0 z-10 bg-[#101f33]">

                          <tr className="border-b border-white/10">

                            <th className="whitespace-nowrap px-4 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
                              Booth
                            </th>

                            <th className="min-w-[420px] whitespace-nowrap px-4 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
                              Polling Station
                            </th>

                            {boothYears.map((year) => (
                              <th
                                key={year}
                                className="whitespace-nowrap px-4 py-4 text-center text-xs font-semibold uppercase tracking-wider text-slate-400"
                              >
                                {year}
                              </th>
                            ))}

                          </tr>

                        </thead>

                        <tbody className="divide-y divide-white/5">

                          {booths.map((booth) => (
                            <tr
                              key={booth.id}
                              className="transition hover:bg-white/[0.03]"
                            >

                              <td className="whitespace-nowrap px-4 py-4 text-sm font-medium text-white">
                                {booth.booth_number}
                              </td>

                              <td className="min-w-[420px] px-4 py-4">
                                <div className="text-sm font-semibold leading-5 text-white">
                                  {booth.polling_station || "—"}
                                </div>

                                {booth.area && (
                                  <div className="mt-1 text-xs leading-5 text-slate-500">
                                    {booth.area}
                                  </div>
                                )}
                              </td>

                              {boothYears.map((year) => {
                                const winner = getWinnerForYear(booth, year);

                                return (
                                  <td
                                    key={`${booth.id}-${year}`}
                                    className={`px-4 py-4 text-center text-sm font-semibold ${getWinnerPartyClass(
                                      winner
                                    )}`}
                                  >
                                    {winner || "—"}
                                  </td>
                                );
                              })}

                            </tr>
                          ))}

                        </tbody>

                      </table>

                    </div>

                  </div>
                )}

              </section>

            </>
          )}

        {!reportLoading &&
          !reportError &&
          selectedSeat &&
          !seatReport?.report && (
            <>
              <section className="mt-6 rounded-2xl border border-white/10 bg-[#0c192b] p-6">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                  Constituency Intelligence
                </p>

                <h3 className="mt-1 text-xl font-semibold">
                  No Report Available
                </h3>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  No constituency report has been uploaded for
                  the selected seat yet.
                </p>
              </section>

            </>
          )}

      </div>
    </main>
  );
}

/* ============================================================
   STAT CARD
   ============================================================ */

function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#101f33] p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">
        {title}
      </p>

      <p className="mt-3 text-2xl font-bold text-white">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}