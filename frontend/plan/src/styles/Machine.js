import React from "react";
import machineIMG from "../img/exampleMachine.png";

import "../App.css";

const machineOverlayTextStyle = {
    color: "white",
    position: "absolute",
    top: "50%",
    left: "50%",
    width: "80%",
    fontSize: "15px",
    textAlign: "center",
    transform: "translateX(-50%) translateY(-50%)",
};

const idStyle = {
    fontSize: "20px",
};

class Machine extends React.Component {
    render() {
        const { name } = this.props;
        const { id } = this.props;
        const imageClick = () => {
            window.open(`https://m.polyup.com/${id}`);
        };
        return (
            <div className="machine">
                <img onClick={() => imageClick()} width="100%" alt="" className="machineImg" src={require(`../img/machines/${this.props.id}.png`)} />
                <div onClick={() => imageClick()} className="machineImgOverlay">
                    <div style={machineOverlayTextStyle}>
                        <div style={idStyle}>
                            {" "}
                            <b>
Machine ID:
                                {this.props.id}
                                {" "}

                            </b>
                        </div>
                        <div>
                            {" "}
                            {this.props.description}
                        </div>
                    </div>

                </div>
            </div>
        );
    }
}

export default Machine;
