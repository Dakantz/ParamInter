
import * as d3 from "d3";
import * as fc from "d3fc";
import { DataRepository } from "../../proc/types";
import { MappedData } from "../types";
import { InterpolationResult } from "../../api/Api";
export interface AnnotationData {
    annotations: MappedData[];
    selection: MappedData[];
    interpolation: InterpolationResult
    embeddinging_name: string;
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
export const seriesSvgAnnotation = (data_rep: DataRepository, spyder_size: number, cls: string = 'annotation') => {
    // the underlying component that we are wrapping
    // const d3Annotation = d3.annotation();

    let xScale = d3.scaleLinear();
    let yScale = d3.scaleLinear();

    function createSpyderFor(sel: d3.Selection<any, any, any, any>, data: MappedData[], annotation_cls: string, spyder_size: number) {
        if (!data || !data.length) {
            return;
        }
        let reqests = data.map(dp => data_rep.dps.getDP(dp.index));
        Promise.all(reqests).then((responses) => {
            const projectedData = responses.map((dp, i) => ({
                ...data[i],
                inputs: dp.inputs,
                x: xScale(data[i].x),
                y: yScale(data[i].y)
            }));
            sel.selectAll(`.${annotation_cls}`).remove();
            sel.selectAll(`.${annotation_cls}`)
                .data(projectedData)
                .join("g")
                .attr("class", annotation_cls)
                // .attr("transform", `translate(${xScale.range()[0]}, ${yScale.range()[0]})`)
                .attr("transform", d => `translate(${d.x}, ${d.y})`)
                .append("path")
                .attr('d', (d) => {
                    let input_data = d.inputs;
                    let pieces = input_data.map((value, i) => {
                        let angle = (i / input_data.length) * 2 * Math.PI;
                        let x = Math.cos(angle) * spyder_size * value;
                        let y = Math.sin(angle) * spyder_size * value;
                        return { x, y };
                    });
                    let path = d3.path();
                    path.moveTo(0, 0);
                    pieces.forEach((piece) => path.lineTo(piece.x, piece.y));
                    return path.toString();
                })

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
            createSpyderFor(sel, annotations, cls, spyder_size);
            createSpyderFor(sel, selectionData, 'selection', spyder_size);

            sel.selectAll('.interpolation').remove();
            if (data.interpolation && data.interpolation.projected_outputs && data.interpolation.projected_outputs[data.embeddinging_name]) {
                console.log("Adding interpolation path for embedding:", data.interpolation, data.embeddinging_name);
                sel.selectAll('.interpolation')
                    .data([data.interpolation.projected_outputs[data.embeddinging_name]])
                    .join("g")
                    .attr("class", "interpolation")
                    .append("path")
                    .attr("d", (d) => {
                        return d3.line()
                            .x(d => xScale(d[0]))
                            .y(d => yScale(d[1]))(d as [number, number][]);
                    })
            }
        })
    };

    series.xScale = (...args) => {
        if (!args.length) {
            return xScale;
        }
        xScale = args[0];
        return series;
    };

    series.yScale = (...args) => {
        if (!args.length) {
            return yScale;
        }
        yScale = args[0];
        return series;
    };

    // fc.rebindAll(series, d3Annotation);

    return series;
};