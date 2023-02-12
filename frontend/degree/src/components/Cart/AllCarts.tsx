import {useSelector} from 'react-redux';
import { allCartsList } from '../../styles/CartStyles';
import CartButton from './CartButton';
import { RootState, ICart } from '../../store/configureStore';


const AllCarts = () => {
    const carts = useSelector((store : RootState) => store.entities.carts);
    const allCartsTitle = `All carts ${'(' + carts.length + ')'}:`;

    return (
        <>
            <div className="mt-2"> {allCartsTitle} </div>
            <ul className="list-group mb-2" style={allCartsList}>
                {carts.map((cart : ICart) => (
                    <CartButton cart={cart} />
                ))}
            </ul>
        </>
    )
}

export default AllCarts;