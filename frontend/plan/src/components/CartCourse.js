import React, {Component} from 'react';

class CartCourse extends Component {
    render() {
        return <div>
            <div>
                <h4>{this.props.code}</h4>
                <div>{this.props.name}</div>
            </div>
            <div>
                <div>

                </div>
            </div>
        </div>;
    }
}

export default CartCourse;