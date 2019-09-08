import React, {Component} from 'react';

class CartCourse extends Component {
    render() {
        return <div style={
            {
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-around",
                padding: "0.5rem",
                borderBottom: "1px solid rgb(200, 200, 200)"
            }}
        >
            <div style={{
                flexGrow: "2",
                display: "flex",
                flexDirection: "column",
                maxWidth: "70%",
                textAlign: "center"
            }}>
                <h4>{this.props.code}</h4>
                <div style={{fontSize: "0.6rem"}}>{this.props.name}</div>
            </div>
            <div style={{
                flexGrow: "1",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex"
            }}>
                <div style={{
                    width: "1rem",
                    height: "1rem",
                    borderRadius: "1rem",
                    backgroundColor: "white",
                    border: "1px solid grey"
                }}>

                </div>
            </div>
        </div>;
    }
}

export default CartCourse;