import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";
import styles from "./ResultReportCheck.module.css";
import { useResult } from "context/ResultContext";

function getFeedback(label, score) {
  let analysis = "";
  let improvement = "";

  if (label === "발화속도") {
    if (score >= 85) analysis = "발화 속도가 안정적이며 자연스럽습니다.";
    else if (score >= 70) analysis = "약간 빠른 편입니다. 리듬을 조절해보세요.";
    else if (score >= 50) analysis = "다소 느립니다. 템포를 조절해보세요.";
    else analysis = "발화 속도가 불안정합니다. 천천히 말하는 연습이 필요합니다.";
    improvement = "호흡과 리듬을 일정하게 유지하도록 연습하세요.";
  }

  if (label === "억양") {
    if (score >= 85) analysis = "억양이 자연스럽고 안정적입니다.";
    else if (score >= 70) analysis = "억양이 다소 단조롭습니다.";
    else if (score >= 50) analysis = "억양이 부자연스럽습니다.";
    else analysis = "억양이 매우 단조롭습니다.";
    improvement = "문장 끝의 높낮이와 감정의 강세를 조절해보세요.";
  }

  if (label === "표정") {
    if (score >= 85) analysis = "표정이 자연스럽고 안정적입니다.";
    else if (score >= 70) analysis = "표정이 다소 긴장되어 있습니다.";
    else if (score >= 50) analysis = "표정이 굳어 있습니다.";
    else analysis = "표정이 부자연스럽습니다.";
    improvement = "눈, 입의 움직임을 부드럽게 하며 미소를 유지해보세요.";
  }

  if (label === "시선") {
    if (score >= 85) analysis = "시선이 안정적입니다.";
    else if (score >= 70) analysis = "시선이 약간 흔들립니다.";
    else if (score >= 50) analysis = "시선이 자주 벗어납니다.";
    else analysis = "시선이 불안정합니다.";
    improvement = "카메라 중앙을 바라보는 연습을 해보세요.";
  }

  return { analysis, improvement };
}

export default function InterviewReport() {
  const navigate = useNavigate();
  const context = useResult() || {};
  const analysisData = context.result || {};
  const [activeTab, setActiveTab] = useState("analysis1");

  if (!analysisData || Object.keys(analysisData).length === 0) {
    return <div className={styles.reportContainer}>⚠️ 분석 결과 데이터가 없습니다.</div>;
  }

  const whisper = analysisData.whisper || {};
  const report = analysisData.report || {};

  const getScore = (v, f = 0) =>
    typeof v === "number" ? parseFloat(v.toFixed(1)) : f;

  const scores = {
    발화속도: getScore(whisper.speech_score_value, 0),
    억양: getScore(whisper.pitch_score_value, 0),
    표정: getScore(report.expression_score_value, 0),
    시선: getScore(report.gaze_score_value, 0),
  };

  const tooltipStyle = {
    backgroundColor: "#fff",
    border: "1px solid #ccc",
    borderRadius: "8px",
    fontSize: "13px",
  };

  const ScoreGuide = () => (
    <div className={styles.scoreGuideBox}>
      <h4>🎯 점수 기준 및 의미</h4>
      <ul>
        <li><strong>85~100점:</strong> 매우 안정적이며 자신감 있는 표현</li>
        <li><strong>70~84점:</strong> 전반적으로 양호하나 세부 조정 필요</li>
        <li><strong>50~69점:</strong> 다소 긴장되거나 리듬이 불안정함</li>
        <li><strong>0~49점:</strong> 긴장감이 높고 부자연스러움이 관찰됨</li>
      </ul>
    </div>
  );

  const DonutChart = ({ score, color, label }) => (
    <div style={{ width: "100%", textAlign: "center" }}>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={[
              { name: label, value: score },
              { name: "남은점수", value: 100 - score },
            ]}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            dataKey="value"
          >
            <Cell fill={color} />
            <Cell fill="#E0E0E0" />
          </Pie>
          <Tooltip formatter={(v) => [`${v.toFixed(1)}점`]} contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ fontWeight: 600 }}>
        {label} ({score.toFixed(1)}점)
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      // ---------------------- 원인분석 1 (표정, 시선)
      case "analysis1":
        return (
          <div className={styles.contentLayout}>
            <div className={styles.chartRow}>
              <div className={styles.chartHalf}>
                <DonutChart score={scores.표정} color="#43a047" label="표정" />
                <div className={styles.feedbackBlock}>
                  <p><strong>📘 점수 해석:</strong> {getFeedback("표정", scores.표정).analysis}</p>
                  <p>💡 개선: {getFeedback("표정", scores.표정).improvement}</p>
                </div>
              </div>

              <div className={styles.chartHalf}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={[{ name: "시선", value: scores.시선 }]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} />
                    <Tooltip formatter={(v) => [`${v.toFixed(1)}점`]} />
                    <Bar dataKey="value" barSize={35} fill="#ff5252" />
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ fontWeight: 600, textAlign: "center" }}>
                  시선 ({scores.시선.toFixed(1)}점)
                </div>
                <div className={styles.feedbackBlock}>
                  <p><strong>📘 점수 해석:</strong> {getFeedback("시선", scores.시선).analysis}</p>
                  <p>💡 개선: {getFeedback("시선", scores.시선).improvement}</p>
                </div>
              </div>
            </div>
            <ScoreGuide />
          </div>
        );

      // ---------------------- 원인분석 2 (발화속도, 억양)
      case "analysis2":
        return (
          <div className={styles.contentLayout}>
            <div className={styles.chartRow}>
              <div className={styles.chartHalf}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={[{ name: "발화속도", value: scores.발화속도 }]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} />
                    <Tooltip formatter={(v) => [`${v.toFixed(1)}점`]} />
                    <Bar dataKey="value" barSize={35} fill="#4A90E2" />
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ fontWeight: 600, textAlign: "center" }}>
                  발화속도 ({scores.발화속도.toFixed(1)}점)
                </div>
                <div className={styles.feedbackBlock}>
                  <p><strong>📘 점수 해석:</strong> {getFeedback("발화속도", scores.발화속도).analysis}</p>
                  <p>💡 개선: {getFeedback("발화속도", scores.발화속도).improvement}</p>
                </div>
              </div>

              <div className={styles.chartHalf}>
                <DonutChart score={scores.억양} color="#7E57C2" label="억양" />
                <div className={styles.feedbackBlock}>
                  <p><strong>📘 점수 해석:</strong> {getFeedback("억양", scores.억양).analysis}</p>
                  <p>💡 개선: {getFeedback("억양", scores.억양).improvement}</p>
                </div>
              </div>
            </div>
            <ScoreGuide />
          </div>
        );

      // ---------------------- 종합 분석 (수정된 부분)
      case "content":
        const radarData = [
          { 항목: "발화속도", 점수: scores.발화속도 },
          { 항목: "억양", 점수: scores.억양 },
          { 항목: "표정", 점수: scores.표정 },
          { 항목: "시선", 점수: scores.시선 },
        ];

        return (
          <div className={styles.contentLayout}>
            <div className={styles.fullWidthContent}>
              <ResponsiveContainer width="80%" height={500}>
                <RadarChart
                  cx="50%"
                  cy="55%"
                  outerRadius={200}           // ✅ px로 고정 (비율 오차 제거)
                  data={radarData}
                >
                  <PolarGrid stroke="#ccc" />
                  <PolarAngleAxis dataKey="항목" tick={{ fill: "#333", fontSize: 14 }} />
                  <PolarRadiusAxis
                    angle={90}                // ✅ 축 정렬 기준 고정
                    domain={[0, 100]}         // ✅ 눈금선 정확히 0~100
                    tickCount={6}
                    scale="linear"            // ✅ 로그 스케일 방지
                    stroke="#ccc"
                    tickFormatter={(t) => `${t}`}
                  />
                  <Radar
                    name="점수"
                    dataKey="점수"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                  <Tooltip formatter={(value, name, props) => [`${value}점`, props.payload.항목]} />
                </RadarChart>
              </ResponsiveContainer>

              <ScoreGuide />

              <div className={styles.feedbackBlock}>
                <p><strong>🧭 종합 해석:</strong> 전체적으로 균형 잡힌 표현력이 중요합니다.</p>
                <p>💬 개선: 자연스러운 억양과 안정된 시선, 일정한 발화속도를 함께 연습하세요.</p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={styles.reportContainer}>
      <div className={styles.headerSection}>
        <div className={styles.reportMainButton}>📊 면접 결과 리포트</div>
      </div>

      <div className={styles.backSection}>
        <button className={styles.backButton} onClick={() => navigate(-1)}>
          ← 이전 화면으로 돌아가기
        </button>
      </div>

      <div className={styles.tabSection}>
        <button
          className={`${styles.tabBtn} ${activeTab === "analysis1" ? styles.active : ""}`}
          onClick={() => setActiveTab("analysis1")}
        >
          원인분석1 (표정·시선)
        </button>
        <button
          className={`${styles.tabBtn} ${activeTab === "analysis2" ? styles.active : ""}`}
          onClick={() => setActiveTab("analysis2")}
        >
          원인분석2 (발화속도·억양)
        </button>
        <button
          className={`${styles.tabBtn} ${activeTab === "content" ? styles.active : ""}`}
          onClick={() => setActiveTab("content")}
        >
          종합 분석
        </button>
      </div>

      <div className={styles.mainContentArea}>{renderTabContent()}</div>
    </div>
  );
}

