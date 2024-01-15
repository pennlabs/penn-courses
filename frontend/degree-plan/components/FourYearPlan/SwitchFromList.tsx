import { mdiCheck, mdiMenuDown, mdiMenuUp, mdiPlus, mdiReorderHorizontal, mdiTrashCanOutline } from "@mdi/js";
import Icon from "@mdi/react";
import { useCallback, useRef, useState } from "react"
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import update from 'immutability-helper'

const planTab = {
    width: '20vw',
    color: '#575757', 
    backgroundColor:'#DBE2F5', 
    padding: '5px',
    borderWidth: '0px',
    // boxShadow: '0px 0px 5px 5px rgba(0, 0, 0, 0.05)',
    borderRadius: '3px',
    margin: '12px'
}

export const titleStyle = {
    color: '#575757', 
    fontWeight: '550',
    position: 'relative' as 'relative'
}

const dropDownListStyle = {
    position: 'absolute' as 'absolute',
    zIndex: 10,
    backgroundColor: 'white',
    boxShadow: '0px 0px 10px 10px rgba(0, 0, 0, 0.05)',
    borderRadius: '6px',
    marginTop: '5px',
    // bgcolor: 'background.paper',
    // border: '2px solid #000',
    // boxShadow: 24,
    // padding: '10px'
  };

  const ListItem = ({item, index, moveItem, setCurrent}: any) => {
      let ref = useRef<HTMLInputElement>(null);

      const [{ opacity }, drop] = useDrop(() => ({
          accept: ItemTypes.MAJOR,
          collect: (monitor) => ({
              opacity: !!monitor.isOver() ? 0 : 1
          }),
          hover(item: any, monitor) {
              if (!ref.current) {
                  return
              }
              const dragIndex = item.index
              const hoverIndex = index
              // Don't replace items with themselves
              if (dragIndex === hoverIndex) {
                  return
              }
              // Actually perform the move action
              moveItem(dragIndex, hoverIndex)
              // mutate the monitor item for the sake of performance to avoid expensive index searches
              item.index = hoverIndex
          }
      }), [])
      /** React dnd */
      const [{ isDragging}, drag] = useDrag(() => ({
          type: ItemTypes.MAJOR,
          item: () => {
              return { index }
          },
          canDrag: true,
          collect: (monitor) => ({
          isDragging: !!monitor.isDragging()
          })
      }),[])
      
      drag(drop(ref));

      return (
          <div className="d-flex justify-content-between" style={{...planTab, opacity: opacity}} ref={ref} >
              <div className="ms-2" onClick={(e) => {console.log('choose clicked'); setCurrent(item)}}>
                  {item}
              </div>
              <div className="d-flex">
                  <Icon path={mdiTrashCanOutline} size={0.92} />
                  <Icon path={mdiReorderHorizontal} size={0.92} />
              </div>
          </div>
    )
}
  
  const SwitchFromList = ({current, setCurrent, list, setList, addHandler}:any) => {
    const [showDropDown, setShowDropDown] = useState(false);
    const [editing, setEditing] = useState(false);
    const [newItem, setNewItem] = useState("");

    const handleClickAdd = () => {
        if (addHandler) {
            setShowDropDown(false);
            addHandler();
        }
        else setEditing(true);
    }

    const handleAdd = () => {
        setList([...list, newItem])
        setCurrent(newItem)
        setEditing(false);
    }

    const moveItem = useCallback((dragIndex: number, hoverIndex: number) => {
        setList((prevItems:any) =>
          update(prevItems, {
            $splice: [
              [dragIndex, 1],
              [hoverIndex, 0, prevItems[dragIndex]],
            ],
          }),
        )
      }, [])

    return (
        <div>
            <div>
                <div className="text-bold" style={titleStyle} onClick={() => {setShowDropDown(!showDropDown); setEditing(false);}}>
                    {current}
                    <Icon path={showDropDown ? mdiMenuUp : mdiMenuDown} size={1} />
                </div>
                {showDropDown && 
                    <div style={dropDownListStyle}>
                        {list.map((item:any, index: number) => 
                            <ListItem key={index} index={index} item={item} moveItem={moveItem} setCurrent={setCurrent}/>
                        )}
                        <div className="" style={planTab}>
                            {editing &&
                                <div className="d-flex">
                                    <input style={{backgroundColor:'#DBE2F5', borderWidth: '0px', width: '60%'}} autoFocus type='text' onChange={(e) => setNewItem(e.target.value)}/>
                                    <div className="ms-1" onClick={handleAdd}> <Icon path={mdiCheck} size={0.8}/> </div>
                                </div>}
                            {!editing && 
                                <div className="d-flex justify-content-center" onClick={handleClickAdd}>
                                    <Icon path={mdiPlus} size={0.8} />
                                </div>}
                        </div>
                    </div>
                }
            </div>
        </div>
    )
}

export default SwitchFromList;