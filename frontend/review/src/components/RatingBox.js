import React from "react";
import { getColor } from "../utils/helpers"; 

/**
 * The rating box that display the course ratings out of 4 (ex: 3.7). Only used in the course search page.
 */
export function RatingBox({ rating, label}) {
  const scoreBoxStyle = { // TODO: replace with styled component
    marginLeft: "5px",
    marginRight: "5px",
    height: "60px",
    width: "60px",
    borderRadius: "4px",
    textAlign: "center",
  }
  
  const scoreStyle = {
    color: "white",
    marginTop: "15px",
    fontSize: "20px"
  }
  
  const scoreLabelStyle = {
    fontSize: "15px",
    letterSpacing: "-0.3px",
    marginTop: "16px"
  }

  return (
    <div 
    className={`scorebox ${getColor(rating)}`}
    style={{
        ...scoreBoxStyle,
    }}>
        <p style={scoreStyle}>{rating}</p>
        <p style={scoreLabelStyle}>{label}</p>
    </div>
  );

}