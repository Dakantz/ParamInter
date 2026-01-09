
import * as d3 from "d3";
import * as fc from "d3fc";
import { colorForIndex, DataRepository } from "../../proc/types";
import { HoveredInterpolation, MappedData } from "../types";
import { InterpolationResult } from "../../api/Api";
import { reSpider } from "./utils";
export interface AnnotationData {
    annotations: MappedData[];
    selection: MappedData[];
    interpolations: InterpolationResult[];
    hovered: HoveredInterpolation | null;
    previewed_data: MappedData | null;
    embeddinging_name: string;

}
interface ProjectedData {
    inputs: number[];
    x: number;
    y: number;
    data: any;
    index: number;
}
// if (spyders.value) {
//     d3.select(spyders.value)
//         .selectAll('g')
//         .data(newSelection)
//         .join('g')
//         .attr('transform', (index) => `translate(${embedded_data.embeddings[index][0]}, ${embedded_data.embeddings[index][1]})`)
//         .append('path')
//         .attr('d', (d) => {
//             let input_data = full_data.inputs[d];
//             let pieces = input_data.map((value, i) => {
//                 let angle = (i / input_data.length) * 2 * Math.PI;
//                 let x = Math.cos(angle) * ui_params.spyder_size * value;
//                 let y = Math.sin(angle) * ui_params.spyder_size * value;
//                 return { x, y };
//             });
//             let path = d3.path();
//             path.moveTo(0, 0);
//             pieces.forEach((piece) => path.lineTo(piece.x, piece.y));
//             return path.toString();
//         })

//     redraw();
// }
export const seriesSvgAnnotation = (data_rep: DataRepository, spyder_size: number, cls: string = 'annotation', n_interpolation_subsamples = 4) => {
    // the underlying component that we are wrapping
    // const d3Annotation = d3.annotation();

    let xScale = d3.scaleLinear();
    let yScale = d3.scaleLinear();
    let min_values = data_rep.description?.input_cols.map((col) => data_rep.description?.min_values[col] || 0) || [];
    let max_values = data_rep.description?.input_cols.map((col) => data_rep.description?.max_values[col] || 1) || [];
    function createSpyderFromProjectedData(sel: d3.Selection<any, any, any, any>, data: ProjectedData[], annotation_cls: string, size = spyder_size, color: string | null = null) {
        sel.selectAll(`.${annotation_cls}`).remove();
        if (!data || !data.length) {
            return;
        }
        let spyder_sel = sel.selectAll(`.${annotation_cls}`)
            .data(data)
            .join("g")
            .attr("class", annotation_cls)
            // .attr("transform", `translate(${xScale.range()[0]}, ${yScale.range()[0]})`)
            .attr("transform", d => `translate(${d.x}, ${d.y})`)
            .append("path")
            .attr('d', (d) => {
                let input_data = d.inputs;
                let pieces = input_data.map((value, i) => {
                    let rescaled_value = reSpider(value, min_values[i], max_values[i]);
                    let angle = (i / input_data.length) * 2 * Math.PI;
                    let x = Math.cos(angle) * size * rescaled_value;
                    let y = Math.sin(angle) * size * rescaled_value;
                    return { x, y };
                });
                let path = d3.path();
                path.moveTo(0, 0);
                pieces.forEach((piece, i) => {
                    path.moveTo(0, 0);
                    path.lineTo(piece.x, piece.y);
                    let next_piece = pieces[(i + 1) % pieces.length];
                    path.lineTo(next_piece.x, next_piece.y);
                });
                path.closePath();
                return path.toString();
            })
        if (color) {
            // console.log("Setting color for spyder:", color);
            let light_col = d3.color(color)?.brighter(1)
            if (light_col) {
                light_col.opacity = 0.4;
                spyder_sel.attr("fill", light_col.toString());
                spyder_sel.attr("stroke", color);
            }
        }
    }
    function createSpyderFromPoints(sel: d3.Selection<any, any, any, any>, data: MappedData[], annotation_cls: string, spyder_size: number) {
        sel.selectAll(`.${annotation_cls}`).remove();
        if (!data || !data.length) {
            return;
        }
        let filteredData = data.filter(d => d.x !== undefined && d.y !== undefined);
        let reqests = filteredData.map(dp => data_rep.dps.getDP(dp.index));
        Promise.all(reqests).then((responses) => {
            const projectedData = responses.map((dp, i) => ({
                ...filteredData[i],
                inputs: dp.inputs,
                x: xScale(filteredData[i].x),
                y: yScale(filteredData[i].y)
            }));
            createSpyderFromProjectedData(sel, projectedData, annotation_cls);
            // join(, projectedData).call((selection) => {
            //     selection
            //         .attr("class", "annotation")
            //         .attr("transform", `translate(${xScale.range()[0]}, ${yScale.range()[0]})`)
            // });
        });

    }
    const series = (selection: d3.Selection<SVGGElement, AnnotationData, null, undefined>) => {
        selection.each((data, index, group) => {
            let sel = d3.select(group[index]);
            let annotations = data.annotations;
            let selectionData = data.selection;
            createSpyderFromPoints(sel, annotations, cls, spyder_size);
            createSpyderFromPoints(sel, selectionData, 'selection', spyder_size);
            sel.selectAll('.hovered').remove();

            sel.selectAll('.interpolation').remove();
            sel.selectAll('.interpolation_spyder').remove();
            let interpolated_outputs = [] as [number, number][][];
            if (data.interpolations) {
                // console.log("Adding interpolation path for embedding:", data.interpolations, data.embeddinging_name);
                interpolated_outputs = data.interpolations.map(int => {
                    return int.projected_outputs[data.embeddinging_name] as [number, number][];
                })
            }

            sel.selectAll('.interpolation')
                .data(interpolated_outputs)
                .join("g")
                .attr("class", "interpolation")
                .append("path")
                .attr("stroke", (d, i) => colorForIndex(i, 0))
                .attr("d", (d) => {
                    return d3.line()
                        .x(d => xScale(d[0]))
                        .y(d => yScale(d[1]))(d as [number, number][]);
                })
            // subsample the interpolation data
            data.interpolations?.forEach((int, i) => {
                let indices = d3.range(0, int.inputs.length,
                    Math.ceil(int.inputs.length / n_interpolation_subsamples));
                indices.push(int.inputs.length - 1);
                let projected_smalls = indices.map(idx => {
                    let d = interpolated_outputs[i][idx];
                    return ({
                        x: xScale(d[0]),
                        y: yScale(d[1]),
                        data: d,
                        index: idx, // no index for interpolation points
                        inputs: int.knn_inputs[idx] || [],
                    } as ProjectedData);
                });
                createSpyderFromProjectedData(sel, projected_smalls, `interpolation_spyder_${i}`, spyder_size * 0.6, colorForIndex(i));
            });
            if (data.hovered && data.hovered.index_in_interpolation >= 0 && data.hovered.interpolation_idx >= 0) {
                let i = data.hovered.interpolation_idx;
                let idx = data.hovered.index_in_interpolation;
                let d = interpolated_outputs[i][idx];
                if (d) {
                    let projected_spyder = {
                        x: xScale(d[0]),
                        y: yScale(d[1]),
                        data: d,
                        index: idx, // no index for interpolation points
                        inputs: data.interpolations[i]?.knn_inputs[idx] || [],
                    } as ProjectedData
                    createSpyderFromProjectedData(sel, [projected_spyder], 'interpolation_spyder_hover', spyder_size * 0.8, colorForIndex(i));
                }
            }
            if (data.previewed_data !== null) {
                createSpyderFromPoints(sel, [data.previewed_data], 'hovered', spyder_size * 1.2);
            }
        })
    };
    series.xScale = (...args: [d3.ScaleLinear<number, number>] | []) => {
        if (!args.length) {
            return xScale;
        }
        xScale = args[0];
        return series;
    };

    series.yScale = (...args: [d3.ScaleLinear<number, number>] | []) => {
        if (!args.length) {
            return yScale;
        }
        yScale = args[0];
        return series;
    };

    // fc.rebindAll(series, d3Annotation);

    return series;
};