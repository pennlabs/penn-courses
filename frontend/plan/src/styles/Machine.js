import React from "react";
import machineIMG from "../img/exampleMachine.png";

import "../App.css";

const machineOverlayTextStyle = {
  color:"white",
  position:"absolute",
  top:"50%",
  left:"50%",
  width:"80%",
  fontSize:"15px",
  textAlign:"center",
  transform:"translateX(-50%) translateY(-50%)"
}

const idStyle={
  fontSize:"20px"
}

class Machine extends React.Component{
  render(){
    const name = this.props.name;
    const id = this.props.id;
    const imageClick = () => {
      window.open("https://m.polyup.com/"+id);
    }
    return(
      <div class="machine">
        <img onClick={()=>imageClick()} width="100%" alt="" class="machineImg" src={require("../img/machines/"+this.props.id+".png")}/>
        <div onClick={()=>imageClick()} class="machineImgOverlay">
            <div style={machineOverlayTextStyle}>
                  <div style={idStyle}> <b>Machine ID: {this.props.id} </b></div>
                  <div> {this.props.description}</div>
            </div>

        </div>
      </div>
    )
  }
}

export default Machine;
