import React, {Component} from 'react';
import CartCourse from "./CartCourse";
import {connect} from "react-redux";
import {toggleCheck} from "../actions";

class Cart extends Component {

    render() {
        return <section
            style={{
                background: "white",
                display: "flex",
                flexGrow: "1",
                flexDirection: "column",
                borderRadius: "6px",
                boxShadow: "0 0 5px 0 rgba(200, 200, 200, 0.6)"
            }}
        >
            {this.props.courses.map(({code, name, checked}) =>
                <CartCourse code={code}
                            toggleCheck={() => this.props.toggleCheck(code)}
                            checked={checked}
                            name={name}/>)}
        </section>;
    }

}

const mapStateToProps = ({cart: {cartCourses}}) => ({
    courses: cartCourses.map(({section: {id, name}, checked}) => ({code: id, name: name, checked}))
});

const mapDispatchToProps = dispatch => ({
    toggleCheck: courseId => dispatch(toggleCheck(courseId))
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);