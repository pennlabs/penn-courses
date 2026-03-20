import React, { useEffect, useMemo, useRef, useState } from "react";
import MapGL, {
    Layer,
    NavigationControl,
    Popup,
    Source,
    type LayerProps,
    type MapRef,
} from "react-map-gl/mapbox";
import type { FeatureCollection, Point } from "geojson";
import { Location } from "../../types";

interface MapProps {
    locations: Location[];
    zoom: number;
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
    if (!locations.length) return [39.9515, -75.191];
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

function Map({ locations, zoom }: MapProps) {
    const mapRef = useRef<MapRef | null>(null);
    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
    const mapboxStyleId = process.env.NEXT_PUBLIC_MAPBOX_STYLE_ID || "mapbox/streets-v12";
    const [cursor, setCursor] = useState<string>("");
    const [selected, setSelected] = useState<{
        longitude: number;
        latitude: number;
        id?: string;
        room?: string;
        start?: number;
        end?: number;
        color?: string;
    } | null>(null);

    const mapStyle = useMemo(() => {
        if (mapboxStyleId.startsWith("mapbox://")) return mapboxStyleId;
        return `mapbox://styles/${mapboxStyleId}`;
    }, [mapboxStyleId]);

    const center = useMemo(() => getGeographicCenter(locations), [locations]);
    const points = useMemo(() => separateOverlappingPoints(locations), [locations]);
    const markerGeoJson = useMemo<
        FeatureCollection<Point, { color?: string; id?: string; room?: string; start?: number; end?: number }>
    >(() => {
        return {
            type: "FeatureCollection",
            features: points.map((p) => ({
                type: "Feature",
                properties: {
                    color: p.color,
                    id: p.id,
                    room: p.room,
                    start: p.start,
                    end: p.end,
                },
                geometry: { type: "Point", coordinates: [p.lng, p.lat] },
            })),
        };
    }, [points]);

    const markerLayer = useMemo<LayerProps>(
        () => ({
            id: "pcp-course-markers",
            type: "circle",
            paint: {
                "circle-radius": 6,
                "circle-color": ["coalesce", ["get", "color"], "#878ED8"],
                "circle-stroke-color": "rgba(0,0,0,0.35)",
                "circle-stroke-width": 2,
            },
        }),
        []
    );


    const formatTime = (t?: number) => {
        if (t == null) return "";
        const hours24 = Math.floor(t);
        const minutes = Math.round((t % 1) * 100);
        const period = hours24 >= 12 ? "PM" : "AM";
        const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
        return `${hours12}:${minutes.toString().padStart(2, "0")} ${period}`;
    };

    useEffect(() => {
        if (!mapRef.current) return;
        mapRef.current.flyTo({
            center: [center[1], center[0]],
            zoom,
            essential: true,
        });
    }, [center, zoom]);

    if (!mapboxToken) {
        return (
            <div
                style={{
                    height: "100%",
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#6b7280",
                    fontSize: "0.9rem",
                    background: "#f9fafb",
                    borderRadius: 8,
                }}
            >
                Missing `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN`
            </div>
        );
    }

    return (
        <MapGL
            ref={mapRef}
            mapboxAccessToken={mapboxToken}
            mapStyle={mapStyle}
            initialViewState={{
                latitude: center[0],
                longitude: center[1],
                zoom,
                pitch: 0,
                bearing: 0,
            }}
            style={{ height: "100%", width: "100%" }}
            attributionControl
            dragRotate
            touchPitch
            maxPitch={70}
            interactiveLayerIds={["pcp-course-markers"]}
            cursor={cursor}
            onMouseMove={(e) => {
                const hovering = (e.features?.length || 0) > 0;
                setCursor(hovering ? "pointer" : "");
            }}
            onClick={(e) => {
                const f = e.features?.[0];
                if (!f || f.geometry.type !== "Point") {
                    setSelected(null);
                    return;
                }
                const [lng, lat] = f.geometry.coordinates as [number, number];
                const props = (f.properties || {}) as Record<string, unknown>;
                setSelected({
                    longitude: lng,
                    latitude: lat,
                    id: typeof props.id === "string" ? props.id : undefined,
                    room: typeof props.room === "string" ? props.room : undefined,
                    start: typeof props.start === "number" ? props.start : undefined,
                    end: typeof props.end === "number" ? props.end : undefined,
                    color: typeof props.color === "string" ? props.color : undefined,
                });
            }}
        >
            <NavigationControl showCompass showZoom visualizePitch position="top-left" />

            <Source id="pcp-course-markers-source" type="geojson" data={markerGeoJson}>
                <Layer {...markerLayer} />
            </Source>

            {selected && (
                <Popup
                    longitude={selected.longitude}
                    latitude={selected.latitude}
                    anchor="top"
                    closeButton
                    closeOnClick={false}
                    onClose={() => setSelected(null)}
                    maxWidth="260px"
                >
                    <div style={{ fontSize: "0.85rem", lineHeight: 1.25 }}>
                        {selected.id && (
                            <div style={{ fontWeight: 700, marginBottom: 4 }}>
                                {selected.id.replace(/-/g, " ")}
                            </div>
                        )}
                        {(selected.start != null || selected.end != null) && (
                            <div style={{ marginBottom: 2 }}>
                                {formatTime(selected.start)}{selected.end != null ? `–${formatTime(selected.end)}` : ""}
                            </div>
                        )}
                        {selected.room && <div>{selected.room}</div>}
                    </div>
                </Popup>
            )}
        </MapGL>
    );
};

export default React.memo(Map);
