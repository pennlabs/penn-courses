import React, { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import Marker from "../map/Marker";
import { Location } from "../../types";

interface MapProps {
    locations: Location[];
    zoom: number;
    focusedLocation?: { lat: number; lng: number } | null;
    onMarkerClick?: (loc: { lat: number; lng: number }) => void;
}

function toRadians(degrees: number): number {
    return degrees * (Math.PI / 180);
}

function toDegrees(radians: number): number {
    return radians * (180 / Math.PI);
}

// calculate the center of all locations on the map view to center the map 
function getGeographicCenter(
    locations: Location[]
): [number, number] {
    let x = 0;
    let y = 0;
    let z = 0;

    locations.forEach((coord) => {
        const lat = toRadians(coord.lat);
        const lon = toRadians(coord.lng);

        x += Math.cos(lat) * Math.cos(lon);
        y += Math.cos(lat) * Math.sin(lon);
        z += Math.sin(lat);
    });

    const total = locations.length;

    x /= total;
    y /= total;
    z /= total;

    const centralLongitude = toDegrees(Math.atan2(y, x));
    const centralSquareRoot = Math.sqrt(x * x + y * y);
    const centralLatitude = toDegrees(Math.atan2(z, centralSquareRoot));

    return [centralLatitude ? centralLatitude : 39.9515, centralLongitude ? centralLongitude : -75.1910];
}

function separateOverlappingPoints(points: Location[], offset = 0.0001) {
    const validPoints = points.filter((p) => p.lat !== null && p.lng !== null) as Location[];

    // group points by coordinates
    const groupedPoints: Record<string, Location[]> = {}; 
    validPoints.forEach((point) => {
        const key = `${point.lat},${point.lng}`;
        (groupedPoints[key] ||= []).push(point);
    });

    // adjust overlapping points
    const adjustedPoints = Object.values(groupedPoints).flatMap((group) =>
        group.length === 1
            ? group // no adjustment needed if class in map view doesnt share locations with others
            : group.map((point, index) => {
                /*
                At a high level, if there are multiple classes in map view that have the exact same location, 
                we try to evenly distribute them around a "circle" centered on the original location. 
                The size of the circle is determined by offset. 
                 */
                const angle = (2 * Math.PI * index) / group.length;
                return {
                    ...point,
                    lat: point.lat! + offset * Math.cos(angle),
                    lng: point.lng! + offset * Math.sin(angle),
                };
            })
    );

    // include points with null values
    return adjustedPoints;
}

interface InnerMapProps {
    locations: Location[];
    center: [number, number]
    focusedLocation?: { lat: number; lng: number } | null;
    onMarkerClick?: (loc: { lat: number; lng: number }) => void;
}

// need inner child component to use useMap hook to run on client 
function InnerMap({ locations, center, focusedLocation, onMarkerClick } :InnerMapProps) {
    const map = useMap();

    useEffect(() => {
        if (!map) return;
        const target = focusedLocation ?? { lat: center[0], lng: center[1] };
        map.flyTo(target);
    }, [center[0], center[1], focusedLocation?.lat, focusedLocation?.lng]);     

    return (
        <>
            <TileLayer
                // @ts-ignore
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                maxZoom={19}
            />
            {separateOverlappingPoints(locations).map(({ lat, lng, color, id, start, end, room }, i) => (
                <Marker
                    key={i}
                    lat={lat}
                    lng={lng}
                    color={color}
                    id={id}
                    start={start}
                    end={end}
                    room={room}
                    onClick={onMarkerClick ? () => onMarkerClick({ lat, lng }) : undefined}
                />
            ))}    
        </>
    )

}

function Map({ locations, zoom, focusedLocation, onMarkerClick }: MapProps) {
    const center = getGeographicCenter(locations);
    
    return (
        <MapContainer
            // @ts-ignore
            center={center}
            zoom={zoom}
            zoomControl={false}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
        >
            <InnerMap
                locations={locations}
                center={center}
                focusedLocation={focusedLocation}
                onMarkerClick={onMarkerClick}
            />
        </MapContainer>
    );
};

export default React.memo(Map);
