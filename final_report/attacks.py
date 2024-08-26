def only_in_roi(input, epsilon, data_grad, pixels_in_roi):
    pert_out = input.detach().clone()
    input.detach().clone()
    k = 1
    for i in pixels_in_roi:
        m, n = i[0], i[1]
        pert_out[0, :, m, n] += epsilon * k * data_grad[0, :, m, n].sign()

    return pert_out

def variable_noise(input, epsilon, data_grad, pixels_in_roi, other_pixels, Z):
    pert_out = input.detach().clone()
    input.detach().clone()
    k = 1
    for i in pixels_in_roi:
        m, n = i[0], i[1]
        pert_out[0, :, m, n] += epsilon * k * data_grad[0, :, m, n].sign()

    for j in other_pixels:
        m, n = j[0], j[1]
        pert_out[0, :, m, n] += epsilon / Z * k * data_grad[0, :, m, n].sign()

    return pert_out