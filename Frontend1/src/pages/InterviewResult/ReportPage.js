import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import styles from './ResultReportCheck.module.css';

export default function InterviewReport() {
  const [activeTab, setActiveTab] = useState('analysis1');
  const [analysisData, setAnalysisData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/fersona/api/interview/result') // 실제 API 엔드포인트로 변경 필요
      .then(res => res.json())
      .then(data => setAnalysisData(data))
      .catch(err => console.error('분석 결과 불러오기 실패:', err));
  }, []);

  if (!analysisData) {
    return <div className={styles.reportContainer}>분석 결과를 불러오는 중...</div>;
  }

  const gazePieData = [
    { name: '왼쪽', value: analysisData.gaze_left || 0, color: '#4A90E2' },
    { name: '오른쪽', value: analysisData.gaze_right || 0, color: '#7ED321' },
    { name: '상향', value: analysisData.gaze_up || 0, color: '#F5A623' },
    { name: '하향', value: analysisData.gaze_down || 0, color: '#D0021B' }
  ];

  const gazeBarData = [
    { name: '좌우 균형', value: analysisData.gaze_lr_balance || 0 },
    { name: '상하 균형', value: analysisData.gaze_ud_balance || 0 }
  ];

  // 시선 경고 텍스트 생성
  function getGazeProblems() {
    const problems = [];
    if (gazeBarData[0].value < 50) problems.push('좌우 균형이 부족합니다.');
    if (gazeBarData[1].value < 50) problems.push('상하 균형이 부족합니다.');
    if (problems.length === 0) problems.push('시선 균형에 문제가 없습니다.');
    return problems;
  }

  const expressionPieData = [
    { name: '중립', value: analysisData.expression_neutral || 0, color: '#4A90E2' },
    { name: '행복', value: analysisData.expression_happy || 0, color: '#7ED321' },
    { name: '긴장', value: analysisData.expression_stressed || 0, color: '#F5A623' },
    { name: '기타', value: analysisData.expression_other || 0, color: '#D0021B' }
  ];

  const expressionBarData = analysisData.expression_metrics || [];

  // 표정 경고 텍스트 생성
  function getExpressionProblems() {
    const problems = [];
    if ((analysisData.expression_stressed || 0) > 50) problems.push('긴장 표정이 많습니다.');
    if ((analysisData.expression_happy || 0) < 20) problems.push('행복 표정이 부족합니다.');
    if (problems.length === 0) problems.push('표정 분포에 문제가 없습니다.');
    return problems;
  }

  // 분석 내용 탭 문제 설명
  function getContentProblems() {
    const list = [];
    if (activeTab === 'analysis1') {
      if (gazeBarData[0].value < 50) list.push('좌우 균형이 부족합니다.');
      if (gazeBarData[1].value < 50) list.push('상하 균형이 부족합니다.');
    } else if (activeTab === 'analysis2') {
      expressionBarData.forEach(metric => {
        if (metric.value < 50) list.push(`${metric.name}가 기준 이하입니다.`);
      });
    }
    return list.length > 0 ? list : ['모든 항목이 기준을 만족합니다.'];
  }

  // 각 탭 별 컨텐츠 렌더링
  function renderTabContent() {
    switch (activeTab) {
      case 'analysis1':
        return (
          <div className={styles.contentLayout}>
            <div className={styles.leftSection}>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie data={gazePieData} cx="50%" cy="50%" innerRadius={80} outerRadius={150} dataKey="value">
                    {gazePieData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className={styles.rightSection}>
              {gazePieData.map((entry, idx) => (
                <div key={idx} className={styles.legendRow}>
                  <div className={styles.legendCircle} style={{ backgroundColor: entry.color }} />
                  <span className={styles.legendText}>{entry.name}</span>
                </div>
              ))}
              <div className={styles.problemContainer}>
                {getGazeProblems().map((msg, i) => (
                  <div key={i} className={styles.problemText}>{msg}</div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'analysis2':
        return (
          <div className={styles.contentLayout}>
            <div className={styles.leftSection}>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie data={expressionPieData} cx="50%" cy="50%" innerRadius={80} outerRadius={150} dataKey="value">
                    {expressionPieData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className={styles.rightSection}>
              {expressionPieData.map((entry, idx) => (
                <div key={idx} className={styles.legendRow}>
                  <div className={styles.legendCircle} style={{ backgroundColor: entry.color }} />
                  <span className={styles.legendText}>{entry.name}</span>
                </div>
              ))}
              <div className={styles.problemContainer}>
                {getExpressionProblems().map((msg, i) => (
                  <div key={i} className={styles.problemText}>{msg}</div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'content':
        return (
          <div className={styles.contentLayout}>
            <div className={styles.fullWidthContent}>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={activeTab === 'analysis1' ? gazeBarData : expressionBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#4A90E2" />
                </BarChart>
              </ResponsiveContainer>
              <div className={styles.problemContainer}>
                {getContentProblems().map((msg, i) => (
                  <div key={i} className={styles.problemText}>{msg}</div>
                ))}
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  }

  return (
    <div className={styles.reportContainer}>
      <div className={styles.headerSection}>
        <div className={styles.reportMainButton}>
          <span>📊</span>
          면접 결과 리포트 확인하기
        </div>
      </div>
      <div className={styles.backSection}>
        <button className={styles.backButton} onClick={() => navigate("/report-menu")}>
          ← 메뉴로 돌아가기
        </button>
      </div>
      <div className={styles.tabSection}>
        <button className={`${styles.tabBtn} ${activeTab === 'analysis1' ? styles.active : ''}`} onClick={() => setActiveTab('analysis1')}>원인분석 1</button>
        <button className={`${styles.tabBtn} ${activeTab === 'analysis2' ? styles.active : ''}`} onClick={() => setActiveTab('analysis2')}>원인분석 2</button>
        <button className={`${styles.tabBtn} ${activeTab === 'content' ? styles.active : ''}`} onClick={() => setActiveTab('content')}>분석 내용</button>
      </div>
      <div className={styles.mainContentArea}>
        {renderTabContent()}
      </div>
    </div>
  );
}
