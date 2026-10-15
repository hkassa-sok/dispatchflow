import React, { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  ArrowRight,
  Bike,
  Box,
  Check,
  ChevronDown,
  CircleDot,
  Clock3,
  Layers3,
  LayoutDashboard,
  MapPin,
  Plus,
  Radio,
  Search,
  ShoppingBag,
  Store,
  Truck,
  Users,
  X,
  Zap,
} from "lucide-react";
import "./style.css";

type Driver = {
  id: number;
  name: string;
  available: boolean;
  lat: number;
  lng: number;
};
type Order = {
  id: number;
  customer_id: number;
  merchant_id: number;
  status: string;
  lat: number;
  lng: number;
  prep_minutes: number;
};
type Assignment = {
  id: number;
  order_id: number;
  driver_id: number;
  accepted: boolean;
  score: number;
};
type Merchant = { id: number; name: string; lat: number; lng: number };
type Data = {
  orders: Order[];
  drivers: Driver[];
  assignments: Assignment[];
  merchants: Merchant[];
  customers: { id: number; name: string }[];
};
const empty: Data = {
  orders: [],
  drivers: [],
  assignments: [],
  merchants: [],
  customers: [],
};
const names: Record<string, string> = {
  CREATED: "Created",
  ACCEPTED: "Accepted",
  PREPARING: "Preparing",
  READY_FOR_PICKUP: "Ready for pickup",
  PICKED_UP: "On the way",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
};
const next: Record<string, string> = {
  CREATED: "ACCEPTED",
  ACCEPTED: "PREPARING",
  PREPARING: "READY_FOR_PICKUP",
  READY_FOR_PICKUP: "PICKED_UP",
  PICKED_UP: "DELIVERED",
};
const initials = (name: string) =>
  name
    .split(" ")
    .map((s) => s[0])
    .join("");
const point = (lat: number, lng: number) => ({
  x: 75 + ((lng + 74.012) / 0.045) * 580,
  y: 380 - ((lat - 40.71) / 0.047) * 350,
});
async function request(path: string, body?: unknown, method = "POST") {
  const res = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Please check the submitted fields.",
    );
  }
  return res.json();
}
function App() {
  const [data, setData] = useState<Data>(empty),
    [role, setRole] = useState("Dispatch"),
    [view, setView] = useState("Overview"),
    [filter, setFilter] = useState("Active"),
    [query, setQuery] = useState(""),
    [connected, setConnected] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [modal, setModal] = useState(false),
    [busy, setBusy] = useState(false),
    [simulate, setSimulate] = useState(false),
    [selected, setSelected] = useState<number | null>(null);
  const refresh = useCallback(async () => {
    try {
      const r = await fetch("/api/dashboard");
      if (!r.ok)
        throw new Error("API is unavailable. Check the backend connection.");
      setData(await r.json());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    void refresh();
    let socket: WebSocket;
    let retry: ReturnType<typeof setTimeout>;
    let disposed = false;
    const connect = () => {
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      );
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => {
        if (JSON.parse(e.data).type !== "heartbeat") void refresh();
      };
      socket.onclose = () => {
        setConnected(false);
        if (!disposed) retry = setTimeout(connect, 2000);
      };
    };
    connect();
    const poll = setInterval(refresh, 15000);
    return () => {
      disposed = true;
      clearTimeout(retry);
      clearInterval(poll);
      socket?.close();
    };
  }, [refresh]);
  useEffect(() => {
    if (!simulate) return;
    const timer = setInterval(() => {
      request("/demo/step")
        .then(refresh)
        .catch((e) => {
          setError(e.message);
          setSimulate(false);
        });
    }, 1500);
    return () => clearInterval(timer);
  }, [simulate, refresh]);
  useEffect(() => {
    if (notice) {
      const t = setTimeout(() => setNotice(""), 4000);
      return () => clearTimeout(t);
    }
  }, [notice]);
  async function act(path: string, body?: unknown, method = "POST") {
    setBusy(true);
    try {
      await request(path, body, method);
      await refresh();
      setNotice("Changes saved successfully");
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  const active = data.orders.filter(
    (o) => !["DELIVERED", "CANCELLED"].includes(o.status),
  );
  const available = data.drivers.filter((d) => d.available).length;
  const pending = active.filter(
    (o) =>
      o.status !== "CREATED" &&
      !data.assignments.some((a) => a.order_id === o.id),
  );
  const visible = data.orders.filter(
    (o) =>
      (filter === "All orders" ||
        (filter === "Active"
          ? !["DELIVERED", "CANCELLED"].includes(o.status)
          : o.status === "DELIVERED")) &&
      `#DF-${String(o.id).padStart(4, "0")} ${data.merchants.find((m) => m.id === o.merchant_id)?.name}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const selectedOrder = data.orders.find((o) => o.id === selected);
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="#">
          <span className="brandmark">
            <Layers3 size={22} />
          </span>
          Dispatch<span>Flow</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">D</span>
          <div>
            Demo workspace<small>Manhattan, New York</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        {[
          ["Overview", LayoutDashboard],
          ["Orders", ShoppingBag],
          ["Drivers", Users],
        ].map(([label, Icon]) => (
          <button
            key={label as string}
            className={"nav " + (view === label ? "selected" : "")}
            onClick={() => setView(label as string)}
          >
            <Icon size={18} />
            {label as string}
            {label === "Orders" && (
              <span className="count">{active.length}</span>
            )}
          </button>
        ))}
        <div className="nav-label second">YOUR VIEW</div>
        {["Dispatch", "Customer", "Merchant", "Driver"].map((r) => (
          <button
            key={r}
            className={"nav " + (role === r ? "role-selected" : "")}
            onClick={() => setRole(r)}
          >
            {r === "Dispatch" ? (
              <Radio size={18} />
            ) : r === "Merchant" ? (
              <Store size={18} />
            ) : r === "Driver" ? (
              <Bike size={18} />
            ) : (
              <Users size={18} />
            )}{" "}
            {r}
          </button>
        ))}
        <div className="sidebar-bottom">
          <div className="demo-callout">
            <Zap size={17} />
            <b>Built for the last mile.</b>
            <p>Explore dispatch, track deliveries, and keep orders moving.</p>
            <span>SEEDED DEMO ENVIRONMENT</span>
          </div>
          <div className="profile">
            <span className="avatar dark">AM</span>
            <div>
              Alex Morgan<small>Workspace operator</small>
            </div>
            <ChevronDown size={14} />
          </div>
        </div>
      </aside>
      <main>
        <header>
          <div className="crumb">
            Workspace <span>/</span> <b>{view}</b>
          </div>
          <div className="header-right">
            <span className="environment">DEMO MODE</span>
            <span className="avatar">AM</span>
          </div>
        </header>
        <div className="content">
          <div className="page-title">
            <div>
              <div className="eyebrow">DELIVERY OPERATIONS</div>
              <h1>
                {view === "Overview"
                  ? "Your city. In motion."
                  : view === "Orders"
                    ? "Every order, connected."
                    : "Meet your fleet."}
              </h1>
              <p>
                A live pulse on your deliveries, drivers, and everything in
                between.
              </p>
            </div>
            <button className="primary" onClick={() => setModal(true)}>
              <Plus size={17} /> Create order
            </button>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setError("")} aria-label="Dismiss error">
                <X size={16} />
              </button>
            </div>
          )}
          <div className="stats">
            {[
              {
                title: "Active orders",
                value: active.length,
                icon: Box,
                detail: "Across all delivery stages",
                class: "green",
              },
              {
                title: "Available drivers",
                value: available,
                icon: Bike,
                detail: `${data.drivers.length} drivers in your fleet`,
                class: "blue",
              },
              {
                title: "Awaiting dispatch",
                value: pending.length,
                icon: Clock3,
                detail: "Ready to match with a driver",
                class: "orange",
              },
              {
                title: "Delivered orders",
                value: data.orders.filter((o) => o.status === "DELIVERED")
                  .length,
                icon: Check,
                detail: "Completed in this workspace",
                class: "purple",
              },
            ].map((s) => (
              <div className="stat" key={s.title}>
                <div className="stat-top">
                  {s.title}
                  <span className={"icon " + s.class}>
                    <s.icon size={17} />
                  </span>
                </div>
                <strong>{s.value.toString().padStart(2, "0")}</strong>
                <small>{s.detail}</small>
              </div>
            ))}
          </div>
          {view === "Overview" && (
            <div className="middle">
              <section className="panel map-panel">
                <div className="panel-title">
                  <div>
                    <h2>
                      Live dispatch map{" "}
                      <span className="live">
                        <i /> {connected ? "Live" : "Reconnecting"}
                      </span>
                    </h2>
                    <p>Manhattan delivery zone · schematic view</p>
                  </div>
                  <button
                    className={"subtle " + (simulate ? "running" : "")}
                    onClick={() => setSimulate(!simulate)}
                  >
                    <CircleDot size={15} />
                    {simulate ? "Pause movement" : "Simulate routes"}
                  </button>
                </div>
                <div className="map">
                  <svg
                    viewBox="0 0 760 430"
                    role="img"
                    aria-label="Schematic map of driver and merchant locations in Manhattan"
                  >
                    <defs>
                      <pattern
                        id="blocks"
                        width="64"
                        height="39"
                        patternTransform="rotate(-24)"
                        patternUnits="userSpaceOnUse"
                      >
                        <rect width="64" height="39" fill="#e9ede5" />
                        <rect
                          x="5"
                          y="5"
                          width="53"
                          height="28"
                          rx="2"
                          fill="#f7f8f2"
                        />
                        <path
                          d="M0 0H64M0 0V39"
                          stroke="#fff"
                          strokeWidth="5"
                        />
                      </pattern>
                    </defs>
                    <rect width="760" height="430" fill="#dcebee" />
                    <path
                      d="M68 -30L675 -30 665 500 195 500 122 262Z"
                      fill="url(#blocks)"
                    />
                    <path
                      d="M170 250L485 105M235 420L620 240"
                      stroke="#fff"
                      strokeWidth="12"
                    />
                    <path
                      d="M170 250L485 105M235 420L620 240"
                      stroke="#f3dc9e"
                      strokeWidth="3"
                    />
                    <path d="M390 16L465 0 494 72 420 101Z" fill="#c9dfc3" />
                    <text x="415" y="45" className="park">
                      UNION SQUARE
                    </text>
                    <text
                      x="48"
                      y="310"
                      transform="rotate(-80 48 310)"
                      className="water"
                    >
                      HUDSON RIVER
                    </text>
                    <text x="170" y="336" className="district">
                      TRIBECA
                    </text>
                    <text x="260" y="233" className="district">
                      SOHO
                    </text>
                    <text x="440" y="146" className="district">
                      EAST VILLAGE
                    </text>
                    <text x="430" y="340" className="district">
                      LOWER EAST SIDE
                    </text>
                    {data.assignments.map((a) => {
                      const d = data.drivers.find((d) => d.id === a.driver_id),
                        o = data.orders.find((o) => o.id === a.order_id),
                        m = data.merchants.find((m) => m.id === o?.merchant_id);
                      if (!d || !o || !m) return null;
                      const start = point(d.lat, d.lng),
                        end = point(
                          o.status === "PICKED_UP" ? o.lat : m.lat,
                          o.status === "PICKED_UP" ? o.lng : m.lng,
                        );
                      return (
                        <line
                          key={a.id}
                          x1={start.x}
                          y1={start.y}
                          x2={end.x}
                          y2={end.y}
                          stroke="#16876b"
                          strokeWidth="3"
                          strokeDasharray="6 5"
                        />
                      );
                    })}
                    {data.merchants.map((m) => {
                      const p = point(m.lat, m.lng);
                      return (
                        <g key={m.id} transform={`translate(${p.x},${p.y})`}>
                          <rect
                            x="-13"
                            y="-13"
                            width="26"
                            height="26"
                            rx="8"
                            fill="#fff"
                            stroke="#d2d9cf"
                          />
                          <text textAnchor="middle" y="5" fontSize="16">
                            ⌂
                          </text>
                        </g>
                      );
                    })}
                    {data.drivers.map((d) => {
                      const p = point(d.lat, d.lng);
                      return (
                        <g key={d.id} transform={`translate(${p.x},${p.y})`}>
                          <title>
                            {d.name}: {d.available ? "Available" : "Assigned"}
                          </title>
                          <circle
                            r="18"
                            fill={d.available ? "#16876b" : "#d49738"}
                            opacity=".14"
                          />
                          <circle
                            r="11"
                            fill={d.available ? "#16876b" : "#d49738"}
                            stroke="white"
                            strokeWidth="3"
                          />
                          <text
                            textAnchor="middle"
                            y="4"
                            fill="white"
                            fontSize="10"
                            fontWeight="700"
                          >
                            {d.id}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                  <div className="map-badge">
                    <MapPin size={14} /> Manhattan, NY
                  </div>
                  <div className="map-legend">
                    <span>
                      <i className="green-dot" />
                      Available driver
                    </span>
                    <span>
                      <i className="orange-dot" />
                      Assigned driver
                    </span>
                    <span>
                      <i className="merchant-dot" />
                      Merchant
                    </span>
                  </div>
                </div>
                <div className="map-footer">
                  <span>
                    <Radio size={14} /> {data.assignments.length} active routes
                  </span>
                  <span>Locations update via WebSocket</span>
                </div>
              </section>
              <section className="panel dispatch-panel">
                <div className="panel-title">
                  <div>
                    <h2>
                      Dispatch queue{" "}
                      <span className="queue-count">{pending.length}</span>
                    </h2>
                    <p>The right driver. The right time.</p>
                  </div>
                  <Zap size={19} className="muted" />
                </div>
                <div className="algorithm">
                  <span className="icon green">
                    <Layers3 size={18} />
                  </span>
                  <div>
                    <b>Intelligent matching</b>
                    <small>Distance + pickup readiness</small>
                  </div>
                  <span className="enabled">ON</span>
                </div>
                <div className="queue">
                  {pending.length === 0 ? (
                    <div className="empty">
                      <Check size={25} />
                      <b>All caught up</b>
                      <p>No orders waiting for a driver.</p>
                    </div>
                  ) : (
                    pending.slice(0, 3).map((o) => (
                      <div className="queue-item" key={o.id}>
                        <div className="queue-order">
                          <span className="order-symbol">
                            <ShoppingBag size={18} />
                          </span>
                          <div>
                            <b>DF-{String(o.id).padStart(4, "0")}</b>
                            <small>
                              {
                                data.merchants.find(
                                  (m) => m.id === o.merchant_id,
                                )?.name
                              }
                            </small>
                          </div>
                          <span className="prep">{o.prep_minutes} min</span>
                        </div>
                        <button
                          className="match"
                          disabled={busy || available === 0}
                          onClick={() => act(`/orders/${o.id}/dispatch`)}
                        >
                          Find best driver <ArrowRight size={15} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
                <div className="queue-note">
                  <span className="green-dot" />
                  {available} drivers available for assignment
                </div>
              </section>
            </div>
          )}
          {view !== "Drivers" && (
            <section className="panel orders-panel">
              <div className="panel-title">
                <div>
                  <h2>
                    {role === "Customer"
                      ? "Your orders"
                      : role === "Merchant"
                        ? "Kitchen orders"
                        : role === "Driver"
                          ? "Delivery assignments"
                          : "Order activity"}
                  </h2>
                  <p>
                    {role === "Dispatch"
                      ? "From kitchen to doorstep, all in one place."
                      : `${role} controls · demo workspace`}
                  </p>
                </div>
                <div className="search">
                  <Search size={15} />
                  <input
                    aria-label="Search orders"
                    placeholder="Search orders..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
              </div>
              <div className="filters">
                {["Active", "All orders", "Delivered"].map((f) => (
                  <button
                    className={filter === f ? "active" : ""}
                    key={f}
                    onClick={() => setFilter(f)}
                  >
                    {f}
                    {f === "Active" && <span>{active.length}</span>}
                  </button>
                ))}
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>ORDER</th>
                      <th>MERCHANT</th>
                      <th>STATUS</th>
                      <th>DRIVER</th>
                      <th>PICKUP ESTIMATE</th>
                      <th>ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible
                      .filter(
                        (o) =>
                          role !== "Driver" ||
                          data.assignments.some((a) => a.order_id === o.id),
                      )
                      .map((o) => {
                        const a = data.assignments.find(
                            (a) => a.order_id === o.id,
                          ),
                          d = data.drivers.find((d) => d.id === a?.driver_id);
                        return (
                          <tr key={o.id}>
                            <td>
                              <button
                                className="order-link"
                                onClick={() => setSelected(o.id)}
                              >
                                DF-{String(o.id).padStart(4, "0")}
                              </button>
                              <small>
                                {
                                  data.customers.find(
                                    (c) => c.id === o.customer_id,
                                  )?.name
                                }
                              </small>
                            </td>
                            <td>
                              <span className="merchant-name">
                                <span className="tiny-icon">
                                  <Store size={14} />
                                </span>
                                {
                                  data.merchants.find(
                                    (m) => m.id === o.merchant_id,
                                  )?.name
                                }
                              </span>
                            </td>
                            <td>
                              <span className={"status " + o.status}>
                                <i />
                                {names[o.status]}
                              </span>
                            </td>
                            <td>
                              {d ? (
                                <span className="driver-cell">
                                  <span className="mini-avatar">
                                    {initials(d.name)}
                                  </span>
                                  {d.name}
                                </span>
                              ) : (
                                <span className="muted">Unassigned</span>
                              )}
                            </td>
                            <td>
                              <span className="estimate">
                                <Clock3 size={14} />
                                {a
                                  ? `${a.score.toFixed(1)} min score`
                                  : `${o.prep_minutes} min prep`}
                              </span>
                            </td>
                            <td>
                              <div className="actions">
                                {role === "Dispatch" &&
                                  pending.some((p) => p.id === o.id) && (
                                    <button
                                      disabled={busy}
                                      onClick={() =>
                                        act(`/orders/${o.id}/dispatch`)
                                      }
                                    >
                                      Dispatch <ArrowUpRight size={13} />
                                    </button>
                                  )}
                                {role === "Merchant" &&
                                  ["CREATED", "ACCEPTED", "PREPARING"].includes(
                                    o.status,
                                  ) && (
                                    <button
                                      disabled={busy}
                                      onClick={() =>
                                        act(
                                          `/orders/${o.id}/status`,
                                          { status: next[o.status] },
                                          "PATCH",
                                        )
                                      }
                                    >
                                      {names[next[o.status]]}
                                    </button>
                                  )}
                                {role === "Driver" && a && !a.accepted && (
                                  <button
                                    disabled={busy}
                                    onClick={() =>
                                      act(`/assignments/${a.id}/accept`)
                                    }
                                  >
                                    Accept
                                  </button>
                                )}
                                {role === "Driver" &&
                                  a?.accepted &&
                                  ["READY_FOR_PICKUP", "PICKED_UP"].includes(
                                    o.status,
                                  ) && (
                                    <button
                                      disabled={busy}
                                      onClick={() =>
                                        act(
                                          `/orders/${o.id}/status`,
                                          { status: next[o.status] },
                                          "PATCH",
                                        )
                                      }
                                    >
                                      {o.status === "PICKED_UP"
                                        ? "Complete"
                                        : "Pick up"}
                                    </button>
                                  )}
                                {role === "Customer" &&
                                  [
                                    "CREATED",
                                    "ACCEPTED",
                                    "PREPARING",
                                    "READY_FOR_PICKUP",
                                  ].includes(o.status) && (
                                    <button
                                      disabled={busy}
                                      onClick={() =>
                                        act(
                                          `/orders/${o.id}/status`,
                                          { status: "CANCELLED" },
                                          "PATCH",
                                        )
                                      }
                                    >
                                      Cancel
                                    </button>
                                  )}
                                <button
                                  aria-label={`View order ${o.id}`}
                                  onClick={() => setSelected(o.id)}
                                >
                                  <ArrowRight size={15} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
                {visible.length === 0 && (
                  <div className="empty">
                    <Box size={25} />
                    <b>No orders in this view</b>
                    <p>Create an order to get things moving.</p>
                  </div>
                )}
              </div>
              <div className="table-footer">
                {visible.length} orders in this view
                <span>
                  <span className="green-dot" /> Synced with backend
                </span>
              </div>
            </section>
          )}
          {view === "Drivers" && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>Driver availability</h2>
                  <p>
                    Assignment locks keep each driver on one active delivery.
                  </p>
                </div>
              </div>
              <div className="driver-grid">
                {data.drivers.map((d) => (
                  <div className="driver-card" key={d.id}>
                    <span className="avatar">{initials(d.name)}</span>
                    <h3>{d.name}</h3>
                    <p>
                      {d.lat.toFixed(5)}, {d.lng.toFixed(5)}
                    </p>
                    <button
                      disabled={
                        busy ||
                        data.assignments.some((a) => a.driver_id === d.id)
                      }
                      onClick={() =>
                        act(
                          `/drivers/${d.id}`,
                          { lat: d.lat, lng: d.lng, available: !d.available },
                          "PATCH",
                        )
                      }
                    >
                      {d.available
                        ? "Go offline"
                        : data.assignments.some((a) => a.driver_id === d.id)
                          ? "On a delivery"
                          : "Go available"}
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
          <footer>
            <span>
              <Layers3 size={13} /> DispatchFlow{" "}
              <span className="footer-separator">/</span> Delivering with
              clarity.
            </span>
            <span>FastAPI · PostgreSQL · Redis</span>
          </footer>
        </div>
      </main>
      {notice && (
        <div className="toast" role="status">
          <Check size={16} />
          {notice}
        </div>
      )}
      {modal && (
        <div className="overlay">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-title"
          >
            <div className="panel-title">
              <h2 id="new-title">Create a delivery</h2>
              <button aria-label="Close" onClick={() => setModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                const ok = await act("/orders", {
                  customer_id: Number(f.get("customer")),
                  merchant_id: Number(f.get("merchant")),
                  lat: Number(f.get("lat")),
                  lng: Number(f.get("lng")),
                  prep_minutes: Number(f.get("prep")),
                });
                if (ok) setModal(false);
              }}
            >
              <label>
                Customer
                <select name="customer">
                  {data.customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Merchant
                <select name="merchant">
                  {data.merchants.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-row">
                <label>
                  Destination latitude
                  <input
                    name="lat"
                    type="number"
                    step="any"
                    min="-90"
                    max="90"
                    defaultValue="40.741"
                    required
                  />
                </label>
                <label>
                  Destination longitude
                  <input
                    name="lng"
                    type="number"
                    step="any"
                    min="-180"
                    max="180"
                    defaultValue="-73.982"
                    required
                  />
                </label>
              </div>
              <label>
                Preparation time (minutes)
                <input
                  name="prep"
                  type="number"
                  min="0"
                  max="120"
                  defaultValue="8"
                  required
                />
              </label>
              <button
                className="primary"
                disabled={busy || !data.customers.length}
                type="submit"
              >
                Create order <ArrowRight size={16} />
              </button>
            </form>
          </section>
        </div>
      )}
      {selectedOrder && (
        <div className="overlay">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="detail-title"
          >
            <div className="panel-title">
              <h2 id="detail-title">
                DF-{String(selectedOrder.id).padStart(4, "0")}
              </h2>
              <button aria-label="Close" onClick={() => setSelected(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="detail">
              <span className={"status " + selectedOrder.status}>
                <i />
                {names[selectedOrder.status]}
              </span>
              <h3>Delivery progress</h3>
              {[
                "CREATED",
                "ACCEPTED",
                "PREPARING",
                "READY_FOR_PICKUP",
                "PICKED_UP",
                "DELIVERED",
              ].map((s, i) => (
                <div
                  className={
                    "progress-step " +
                    (i <= Object.keys(next).indexOf(selectedOrder.status) ||
                    selectedOrder.status === "DELIVERED"
                      ? "done"
                      : "")
                  }
                  key={s}
                >
                  <CircleDot size={16} />
                  {names[s]}
                </div>
              ))}
              <p>
                Destination: {selectedOrder.lat.toFixed(4)},{" "}
                {selectedOrder.lng.toFixed(4)}
              </p>
              <p>
                Switch to Merchant to prepare the order, then Driver to accept,
                pick up, and complete the delivery.
              </p>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
