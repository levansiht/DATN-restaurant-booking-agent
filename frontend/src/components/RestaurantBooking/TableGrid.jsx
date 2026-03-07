import { useEffect, useState } from "react";


function getStatusMeta(status) {
  const statusMap = {
    available: {
      label: "Trống",
      card: "border-emerald-300 bg-emerald-50 text-emerald-900 hover:border-emerald-400 hover:bg-emerald-100",
      dot: "bg-emerald-500",
    },
    reserved: {
      label: "Đã giữ",
      card: "border-amber-300 bg-amber-50 text-amber-900 opacity-80",
      dot: "bg-amber-500",
    },
    occupied: {
      label: "Đang dùng",
      card: "border-rose-300 bg-rose-50 text-rose-900 opacity-80",
      dot: "bg-rose-500",
    },
    maintenance: {
      label: "Bảo trì",
      card: "border-stone-300 bg-stone-100 text-stone-700 opacity-75",
      dot: "bg-stone-500",
    },
    "too-small": {
      label: "Nhỏ hơn nhóm",
      card: "border-slate-300 bg-slate-100 text-slate-700 opacity-80",
      dot: "bg-slate-500",
    },
  };

  return statusMap[status] || statusMap.reserved;
}


const TableGrid = ({ floors, selectedTable, onTableSelect, partySize }) => {
  const [activeFloor, setActiveFloor] = useState(floors[0]?.name || "");

  useEffect(() => {
    if (!floors.length) {
      setActiveFloor("");
      return;
    }

    if (!floors.find((floor) => floor.name === activeFloor)) {
      setActiveFloor(floors[0].name);
    }
  }, [activeFloor, floors]);

  const getTableStatus = (table) => {
    const status = String(table.status || "").toLowerCase();

    if (status === "maintenance") {
      return "maintenance";
    }

    if (status === "occupied") {
      return "occupied";
    }

    if (status === "reserved" || status === "booked") {
      return "reserved";
    }

    if (!table.is_available_for_booking) {
      return "reserved";
    }

    if (table.capacity < partySize) {
      return "too-small";
    }

    return "available";
  };

  const currentFloor = floors.find((floor) => floor.name === activeFloor) || floors[0];

  const floorStats = {
    available:
      currentFloor?.tables.filter((table) => getTableStatus(table) === "available").length || 0,
    reserved:
      currentFloor?.tables.filter((table) => getTableStatus(table) === "reserved").length || 0,
    occupied:
      currentFloor?.tables.filter((table) => {
        const status = getTableStatus(table);
        return status === "occupied" || status === "maintenance";
      }).length || 0,
  };

  if (!floors.length) {
    return (
      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white px-6 py-14 text-center text-sm text-stone-500">
        Chưa có sơ đồ bàn để hiển thị.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {floors.map((floor) => (
          <button
            key={floor.name}
            type="button"
            onClick={() => setActiveFloor(floor.name)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              activeFloor === floor.name
                ? "bg-[#8b2328] text-white shadow-[0_10px_24px_rgba(139,35,40,0.24)]"
                : "border border-stone-200 bg-white text-stone-600 hover:border-stone-300 hover:text-stone-900"
            }`}
          >
            {floor.name}
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { key: "available", label: "Bàn trống", value: floorStats.available },
          { key: "reserved", label: "Đã giữ chỗ", value: floorStats.reserved },
          { key: "occupied", label: "Đang bận", value: floorStats.occupied },
        ].map((item) => (
          <div
            key={item.key}
            className="rounded-[1.5rem] border border-stone-200 bg-white px-5 py-4 shadow-sm"
          >
            <div className="text-sm text-stone-500">{item.label}</div>
            <div className="mt-2 text-3xl font-semibold text-stone-900">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_18px_60px_rgba(61,43,30,0.06)]">
        <div className="flex flex-col gap-3 border-b border-stone-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-stone-500">
              Floor Plan
            </div>
            <h3 className="jp-display mt-2 text-3xl font-semibold text-stone-900">
              {currentFloor?.name}
            </h3>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-stone-500">
            {["available", "reserved", "occupied", "too-small"].map((statusKey) => {
              const statusMeta = getStatusMeta(statusKey);
              return (
                <div key={statusKey} className="inline-flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${statusMeta.dot}`}></span>
                  {statusMeta.label}
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          {currentFloor?.tables?.map((table) => {
            const status = getTableStatus(table);
            const statusMeta = getStatusMeta(status);
            const isSelected = selectedTable?.id === table.id;
            const isSelectable = status === "available";

            return (
              <button
                key={table.id}
                type="button"
                onClick={() => isSelectable && onTableSelect(table)}
                className={`relative min-h-[150px] rounded-[1.6rem] border p-4 text-left transition ${
                  isSelected
                    ? "border-[#8b2328] bg-[#fff5f2] text-[#531317] shadow-[0_20px_40px_rgba(139,35,40,0.18)]"
                    : statusMeta.card
                } ${isSelectable ? "hover:-translate-y-1" : "cursor-not-allowed"}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] opacity-70">
                      Table
                    </div>
                    <div className="mt-1 text-2xl font-semibold">T{table.id}</div>
                  </div>
                  <span className={`h-2.5 w-2.5 rounded-full ${statusMeta.dot}`}></span>
                </div>

                <div className="mt-5 space-y-1 text-sm">
                  <div>{table.table_type}</div>
                  <div>Sức chứa {table.capacity} khách</div>
                  <div className="font-medium">{statusMeta.label}</div>
                </div>

                {table.notes && (
                  <div className="mt-4 line-clamp-2 text-xs opacity-70">{table.notes}</div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {selectedTable && (
        <div className="rounded-[1.75rem] border border-[#dcb889] bg-[linear-gradient(135deg,_#fff7eb,_#fffdf8)] p-5 shadow-[0_18px_50px_rgba(92,69,44,0.08)]">
          <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
            Selected Table
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-4">
            <div>
              <div className="text-sm text-stone-500">Mã bàn</div>
              <div className="mt-1 text-lg font-semibold text-stone-900">T{selectedTable.id}</div>
            </div>
            <div>
              <div className="text-sm text-stone-500">Loại bàn</div>
              <div className="mt-1 text-lg font-semibold text-stone-900">{selectedTable.table_type}</div>
            </div>
            <div>
              <div className="text-sm text-stone-500">Tầng</div>
              <div className="mt-1 text-lg font-semibold text-stone-900">{selectedTable.floor}</div>
            </div>
            <div>
              <div className="text-sm text-stone-500">Sức chứa</div>
              <div className="mt-1 text-lg font-semibold text-stone-900">{selectedTable.capacity} khách</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableGrid;
