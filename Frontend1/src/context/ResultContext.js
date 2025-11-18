import React, { createContext, useContext, useState } from "react";

const ResultContext = createContext(null); // <- 현재 null

export const ResultProvider = ({ children }) => {
  const [result, setResult] = useState(null); // 분석 결과 저장

  return (
    <ResultContext.Provider value={{ result, setResult }}>
      {children}
    </ResultContext.Provider>
  );
};

export const useResult = () => {
  const context = useContext(ResultContext);
  if (!context) {
    throw new Error("useResult must be used within a ResultProvider");
  }
  return context;
};