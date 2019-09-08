import React, {Component} from 'react';
import CartCourse from "./CartCourse";

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
            {this.props.courses.map(({code, name}) =>
                <CartCourse code={code}
                    name={name}/>)}
        </section>;
    }

}

export default Cart;