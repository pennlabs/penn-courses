import React, {Component} from 'react';
import PropTypes from "prop-types";
import "../styles/course-cart.css";

class CartCourse extends Component {

    constructor(props) {
        super(props);
        this.state = {checked: false};
    }

    toggleCheck = () => {
        this.setState(({checked}) => ({checked: !checked}));
    };

    render() {
        const checkStyle = {
            width: "1rem",
            height: "1rem",
            borderRadius: "1rem",
            backgroundColor: "white",
            border: "1px solid grey"
        };
        return <div
            className={"course-cart-item"}
            style={
                {
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "space-around",
                    padding: "0.8rem",
                    borderBottom: "1px solid rgb(200, 200, 200)"
                }}
            onClick={this.toggleCheck}
        >
            <div style={{
                flexGrow: "2",
                display: "flex",
                flexDirection: "column",
                maxWidth: "70%",
                textAlign: "left",
                alignItems: "left"
            }}>
                <h4>{this.props.code}</h4>
                <div style={{fontSize: "0.6rem"}}>{this.props.name}</div>
            </div>
            <div style={{
                flexGrow: "0",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex"
            }}>
                {this.state.checked ?
                    <i className="fas fa-check-circle" style={
                        {
                            ...checkStyle,
                            border: "none",
                            color: "#878ED8"
                        }
                    }/> :
                    <div style={checkStyle}/>}
            </div>
        </div>;
    }
}

CartCourse.propTypes = {
    name: PropTypes.string.isRequired,
    code: PropTypes.string.isRequired
};

export default CartCourse;