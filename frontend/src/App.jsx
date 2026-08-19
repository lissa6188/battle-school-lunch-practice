import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export default function App() {
  const [query, setQuery] = useState("");
  const [schools, setSchools] = useState([]);
  const [selected, setSelected] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [meals, setMeals] = useState([]);
  const [error, setError] = useState("");

  async function search() {
    setError("");
    if (query.length < 2) {
      setError("검색어는 최소 2자 이상 입력하세요.");
      return;
    }
    const res = await fetch(`${API_BASE}/schools?query=${encodeURIComponent(query)}`);
    if (!res.ok) {
      setError("검색 중 오류가 발생했습니다.");
      return;
    }
    const data = await res.json();
    setSchools(data);
  }

  async function fetchMeals() {
    setError("");
    if (!selected) {
      setError("학교를 선택하세요.");
      return;
    }
    if (!startDate || !endDate) {
      setError("시작일과 종료일을 모두 지정하세요.");
      return;
    }
    const res = await fetch(
      `${API_BASE}/meals?school_code=${selected.code}&start_date=${startDate}&end_date=${endDate}`
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(body.detail || "조회 중 오류가 발생했습니다.");
      return;
    }
    const data = await res.json();
    setMeals(data);
  }

  return (
    <div className="container">
      <h1>급식 배틀</h1>

      <section className="search">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="학교명 일부 입력" />
        <button onClick={search}>검색</button>
        {error && <div className="error">{error}</div>}
        <ul className="schools">
          {schools.map((s) => (
            <li key={s.code} onClick={() => setSelected(s)} className={selected?.code === s.code ? "selected" : ""}>
              {s.name} <small>{s.address}</small>
            </li>
          ))}
        </ul>
      </section>

      <section className="filter">
        <label>
          시작일
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </label>
        <label>
          종료일
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </label>
        <button onClick={fetchMeals}>조회</button>
      </section>

      <section className="results">
        <h2>결과</h2>
        {meals.length === 0 && <div>조회된 급식 정보가 없습니다.</div>}
        <ul>
          {meals.map((m) => (
            <li key={m.date} className="meal-card">
              <div className="meal-date">{m.date}</div>
              <div className="meal-school">{m.school_name}</div>
              <div className="meal-menu">{m.lunch ? m.lunch.join(" · ") : "급식 정보가 없습니다."}</div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
