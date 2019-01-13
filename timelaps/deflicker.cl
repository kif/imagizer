kernel void mean2std(global float* value,
                     global float2* mean,
                     global float* delta2,
                     int size)
{
    int gid = get_global_id(0);
    if (gid>=size)
    {
       return;
    }
    float m = mean[0].s0/mean[0].s1;
    float delta = value[gid] - m;
    delta2[gid] = delta * delta;
}

kernel void sigmaclip(global float* value,
                       global float2* mean,
                       global float2* std,
                       float cutof,                 
                       int size)
{
    int gid = get_global_id(0);
    if (gid>=size)
    {
       return; 
    }
       
    float m = mean[0].s0 / mean[0].s1;
    float s = sqrt(std[0].s0 / (std[0].s1 - 1.0f));
    if (fabs(value[gid]-m)>(cutof*s))
    {
        value[gid] = NAN;
    }
}

static float dec_sRGB(uchar value)
{
    float res, a=0.055f, gamma=2.4f,slope=12.92f; 
    if (value<=10)
        res = (float)value/255.0f/slope;
    else
        res = pow(((float)value/255.0f + a)/(1.0f+a), gamma);
    return res;
}

static uchar comp_sRGB(float value)
{
    float a=0.055f, gamma=2.4f,slope=12.92f, c=0.0031308f; 
    float res;
    if (value<=c)
        res = value*slope;
    else
        res = (1.0f+a) * powr(value, 1.0f/gamma) - a;
    if (res<0.0f)
        res = 0.0f;
    else if (res>1.0f)
        res = 255.0f;
    else
        res = 255.0f*res + 0.5f;
    
    return (uchar) res;
}

static float comp_L(float value)
{ //https://fr.wikipedia.org/wiki/CIE_L*a*b*

    float epsilon = 216.0f/24389.0f,
          kappa = 24389.0f/27.0f,
          res;
    if (value>epsilon)
        res = pow(value, 1.0f/3.0f);
    else
        res = (kappa * value + 16.0f)/ 116.0f;
    return res;
}

static float dec_L(float value)
{
    float d = 6.0f/29.0f, res;
    if (value>d)
        res = pown(value, 3);
    else
        res = (value - 4.0f/29.0f) * 3.0f * d * d;
    return res;
}

static float3 XYZ2Lab(float3 XYZ)
{
    float3 Lab, 
           D65 = (float3)(0.9504f,  1.0000f, 1.0888f),
           xyz = XYZ/D65,
           fxyz = (float3)(comp_L(xyz.x), comp_L(xyz.y), comp_L(xyz.z));
    Lab = (float3)(116.0f * fxyz.y - 16.0f,
                   500 * (fxyz.x - fxyz.y),
                   200 * (fxyz.y - fxyz.z));
    return Lab;
}

static float3 Lab2XYZ(float3 Lab)
{
    float3 D65 = (float3)(0.9504f,  1.0000f, 1.0888f),
           xyz;
    float l;
           
    l = (Lab.x + 16.0f)/116.0f;
    xyz = (float3)(dec_L(l + Lab.y/500.0f),
                   dec_L(l),
                   dec_L(l - Lab.z/200.0f));
    return xyz * D65;
}

static float3 RGB2XYZ(float3 RGB)
{
    //const float matrix[9] = {0.4124f, 0.3576f, 0.1805f, 0.2126f, 0.7152f, 0.0722f, 0.0193f, 0.1192f, 0.9505f};
    const float3 to_X = (float3)(0.4124f, 0.3576f, 0.1805f);
    const float3 to_Y = (float3)(0.2126f, 0.7152f, 0.0722f);
    const float3 to_Z = (float3)(0.0193f, 0.1192f, 0.9505f);
    return (float3)(dot(RGB, to_X), dot(RGB, to_Y), dot(RGB, to_Z));
}

static float3 XYZ2RGB(float3 XYZ)
{
    //const float matrix[9] = {3.2410f, -1.5374f, -0.4986f, -0.9692f,  1.8760f,  0.0416f, 0.0556f, -0.2040f,  1.0570f};
    const float3 to_R = (float3)( 3.2410f,-1.5374f,-0.4986f),
                 to_G = (float3)(-0.9692f, 1.8760f, 0.0416f),
                 to_B = (float3)( 0.0556f,-0.2040f,1.0570f);
    return (float3)(dot(XYZ, to_R), dot(XYZ, to_G), dot(XYZ, to_B));
}


kernel void decompress_sRGB(global uchar *sRGB, global float *RGB, int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = 3*(get_global_id(0) + width * get_global_id(1));
        RGB[i] = dec_sRGB(sRGB[i]);
        RGB[i+1] = dec_sRGB(sRGB[i+1]);
        RGB[i+2] = dec_sRGB(sRGB[i+2]);
    }
}

kernel void compress_sRGB(global float *RGB, global uchar *sRGB, int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = 3*(get_global_id(0) + width * get_global_id(1));
        RGB[i] = comp_sRGB(sRGB[i]);
        RGB[i+1] = comp_sRGB(sRGB[i+1]);
        RGB[i+2] = comp_sRGB(sRGB[i+2]);
    }
}

kernel void sRGB_to_Lab(global uchar *sRGB, global float *Lab, int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        float3 RGB, XYZ, LAB;

        int i = 3*(get_global_id(0) + width * get_global_id(1));
        RGB = (float3)(dec_sRGB(sRGB[i]),
                       dec_sRGB(sRGB[i+1]),
                       dec_sRGB(sRGB[i+2]));
        XYZ = RGB2XYZ(RGB);
        LAB = XYZ2Lab(XYZ);
        Lab[i] = LAB.x;
        Lab[i+1] = LAB.y;
        Lab[i+2] = LAB.z;
    }
}

kernel void Lab_to_sRGB(global float *Lab, global uchar *sRGB, int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        float3 RGB, XYZ, LAB;

        int i = 3*(get_global_id(0) + width * get_global_id(1));
        LAB = (float3)(Lab[i], Lab[i+1], Lab[i+2]);
        XYZ = Lab2XYZ(LAB);
        RGB = XYZ2RGB(XYZ);
        sRGB[i] = comp_sRGB(RGB.x);
        sRGB[i+1] = comp_sRGB(RGB.y);
        sRGB[i+2] = comp_sRGB(RGB.z);
    }
}


kernel void convert_color(global float *RGB, global float *XYZ, int width, int height, global float *matrix)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = get_global_id(0) + width * get_global_id(1);
        XYZ[3*i+0] = RGB[3*i]*matrix[0] + RGB[3*i+1]*matrix[1] + RGB[3*i+2]*matrix[2];
        XYZ[3*i+1] = RGB[3*i]*matrix[3] + RGB[3*i+1]*matrix[4] + RGB[3*i+2]*matrix[5];
        XYZ[3*i+2] = RGB[3*i]*matrix[6] + RGB[3*i+1]*matrix[7] + RGB[3*i+2]*matrix[8];
    }
}

kernel void sRGB_to_RGB(global uchar *sRGB, global float *RGB, int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        float3 RGB3;

        int i = 3*(get_global_id(0) + width * get_global_id(1));
        RGB3 = (float3)(dec_sRGB(sRGB[i]),
                       dec_sRGB(sRGB[i+1]),
                       dec_sRGB(sRGB[i+2]));
        RGB[i] = RGB3.x;
        RGB[i+1] = RGB3.y;
        RGB[i+2] = RGB3.z;
    }
}

// load a float3 from a given prosition:
static float3 load3(global float* image,
                    int index)
{
    float3 res = (float3)(image[3*index], image[3*index+1], image[3*index+2]);
    return res;
}

//Perform a bilinear interpolation of image with 3 channels
static float3 bilinear3(float2 target, 
                        global float* image,
                        int2 size,
                        float3 fill,
                        int mode) //mode = 1 bilinear or 0 for nearest
{
    int tx_prev = (int) target.x,
        tx_next = tx_prev + 1,
        ty_prev = (int) target.y,
        ty_next = ty_prev + 1;

    float3 interp = fill;

    if (0.0f <= target.x && target.x < (size.x - 1) && 0.0f <= target.y && target.y < (size.y - 1) )
    {
        if (mode == 1) 
        {   //bilinear interpolation: read 4 neighbours
            float3 image_p = load3(image, ty_prev*size.x + tx_prev),
                   image_x = load3(image, ty_prev*size.x + tx_next),
                   image_y = load3(image, ty_next*size.x + tx_prev),
                   image_n = load3(image, ty_next*size.x + tx_next);

            if (tx_next >= size.x) 
            {
                image_x = image_p;
                image_n = image_y;
            }
            if (ty_next >= size.y) {
                image_y = image_p;
                image_n = image_x;
            }

            //bilinear interpolation
            float3 interp1 = ((float) (tx_next - target.x)) * image_p + ((float) (target.x - tx_prev)) * image_x,
                   interp2 = ((float) (tx_next - target.x)) * image_y + ((float) (target.x - tx_prev)) * image_n;

            interp = ((float) (ty_next - target.y)) * interp1 + ((float) (target.y - ty_prev)) * interp2;

        }
        else 
        { //no interpolation TODO: round index !
                interp = load3(image, (int)(target.y + 0.5f) * size.x + (int)(target.x + 0.5f));
        }
    }
    
    //to be coherent with scipy.ndimage.interpolation.affine_transform
    if (target.x >= (size.x - 1)) 
        interp = fill;
    if (target.y >= (size.y - 1)) 
            interp = fill;
    return interp;
}

static float _lanczos_n(float value, float order)
{
    float res=0.0f;
    if (value == 0)
        res = 1.0f;
    else if (fabs(value)>=order)
        res = 0.0f;
    else
        res = order*sin(M_PI_F*value)*sin(M_PI_F*value/order)/(M_PI_F*M_PI_F*value*value);
    return res;
}

//Perform a lanczos interpolation of image with 3 channels, mode may be 
static float3 lanczos(float2 target, 
                      global float* image,
                      int2 size,
                      float2 scale, 
                      float3 fill,
                      int mode) //mode = 1, 2 or 3 for width of the filter
{
    if ((target.x < 0)||target.x > (size.x - 1)||(target.y < 0)||target.y > (size.y - 1))
    {
        return fill;
    }
        
    float4 sum4 = (float4)(0.0f, 0.0f, 0.0f, 0.0f);
    float coef_x, coef_y, coef, fmode=(float) mode;
    int xmin, xmax, ymin, ymax, x, y, idx;
    xmin = max((int)floor(target.x - scale.x * fmode), 0);
    xmax = min((int) ceil(target.x + scale.x * fmode) + 1, size.x);
    ymin = max((int)floor(target.y - scale.y * fmode), 0);
    ymax = min((int) ceil(target.y + scale.y * fmode) + 1, size.y);
    
    for (y=ymin; y<ymax; y++)
    {
        coef_y = _lanczos_n(((float)y-target.y)/scale.y, fmode);
        for (x=xmin; x<xmax; x++)    
        {
            coef_x = _lanczos_n(((float)x-target.x)/scale.x, fmode);
            idx = y * size.x + x;
            coef = coef_x * coef_y;
            if (fabs(coef)>1.0e-30f)
            {
                sum4 += (float4)(load3(image, idx) * coef, coef);
            }
            
        }
    }
    return (float3)(sum4.s0/sum4.s3, sum4.s1/sum4.s3, sum4.s2/sum4.s3);
}

kernel void rotate_image(global float *inp, global float *out, int width, int height, float angle)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        float cx = width/2.0f, cy = height/2.0f, xout, yout;
        xout = (float) get_global_id(0);
        yout = (float) get_global_id(1);
        
        float2 target = (float2)(cos(angle)*(xout - cx) + sin(angle)*(yout - cy) + cx,
                                -sin(angle)*(xout - cx) + cos(angle)*(yout - cy) + cy);
        int i = get_global_id(0) + width * get_global_id(1);
        float3 out3= bilinear3(target, 
                               inp,
                               (int2)(width, height),
                               (float3) (0.0f, 0.0f, 0.0f),
                               1);
        out[3*i] = out3.x;
        out[3*i+1] = out3.y;
        out[3*i+2] = out3.z;
    }
}

kernel void unwrap_image(global float *inp, global float *out, 
                         int width_dis, int height_dis,
                         int width_cor, int height_cor,
                         float center_dis_x, float center_dis_y,
                         float center_cor_x, float center_cor_y,
                         float k1, float k2, float k3)
{
    if ((get_global_id(0)<width_cor) && (get_global_id(1) < height_cor))
    {
        float xcor, ycor, r2, correction;
        xcor = (float) get_global_id(0) - center_cor_x;
        ycor = (float) get_global_id(1) - center_cor_y;
        r2 = xcor*xcor + ycor*ycor;
        //K1 = arg[8]*1e-9
        //K2 = arg[9]*1e-15
        //K3 = arg[10]*1e-23
        //return c + (u - c)*
        correction = (1.0f + k1*r2 + k2*r2*r2 + k3*r2*r2*r2);
        float2 target = (float2)(center_dis_x + xcor*correction,
                                 center_dis_y + ycor*correction);
        int i = get_global_id(0) + width_cor * get_global_id(1);
        float3 out3= bilinear3(target, 
                               inp,
                               (int2)(width_dis, height_dis),
                               (float3) (0.0f, 0.0f, 0.0f),
                               1);
        out[3*i] = out3.x;
        out[3*i+1] = out3.y;
        out[3*i+2] = out3.z;
    }
}

kernel void unwrap_rot_image(global float *inp, global float *out, 
                         int width_dis, int height_dis,
                         int width_cor, int height_cor,
                         float center_dis_x, float center_dis_y,
                         float center_cor_x, float center_cor_y,
                         float k1, float k2, float k3, float angle, 
                         float fill)
{
    if ((get_global_id(0)<width_cor) && (get_global_id(1) < height_cor))
    {
        float xcor, ycor, r2, correction, xcorr, ycorr;
        xcor = (float) get_global_id(0) - center_cor_x;
        ycor = (float) get_global_id(1) - center_cor_y;
        r2 = xcor*xcor + ycor*ycor;
        correction = (1.0f + k1*r2 + k2*r2*r2 + k3*r2*r2*r2);
        xcorr = cos(angle) * xcor - sin(angle) * ycor;
        ycorr = sin(angle) * xcor + cos(angle) * ycor;
        float2 target = (float2)(center_dis_x + xcorr*correction,
                                 center_dis_y + ycorr*correction);
        int i = get_global_id(0) + width_cor * get_global_id(1);
        float3 out3= bilinear3(target, 
                               inp,
                               (int2)(width_dis, height_dis),
                               (float3) (fill, fill, fill),
                               1);
        out[3*i] = out3.x;
        out[3*i+1] = out3.y;
        out[3*i+2] = out3.z;
    }
}

kernel void decimate(global float *inp, global float *out, 
                      int width_inp, int height_inp,
                      int width_out, int height_out,
                      float offset_x, float offset_y,
                      float decimation_x, float decimation_y,
                      int mode, float fill)
{
    if ((get_global_id(0)<width_out) && (get_global_id(1) < height_out))
    {
        float xin, yin;
        float3 out3;
        xin = (float) get_global_id(0) * decimation_x + offset_x;
        yin = (float) get_global_id(1) * decimation_y + offset_y;
        float2 target = (float2)(xin, yin);
        int i = get_global_id(0) + width_out * get_global_id(1);
        
        if (mode<2)
            out3 = bilinear3(target, 
                             inp,
                             (int2)(width_inp, height_inp),
                             (float3) (fill, fill, fill),
                             mode);
        else
            out3 = lanczos(target, 
                           inp,
                           (int2)(width_inp, height_inp),
                           (float2)(decimation_x, decimation_y), 
                           (float3) (fill, fill, fill),
                           mode);
        out[3*i] = out3.x;
        out[3*i+1] = out3.y;
        out[3*i+2] = out3.z;
    }
}

kernel void sinc(global float* data, float scale, float order)
{
    int center = (get_global_size(0) - 1)/2;
    int pos = get_global_id(0) - center;
    data[get_global_id(0)] = _lanczos_n((float)pos/scale, order);

}

kernel void normalize_LAB(global float *LAB, int width, int height, float normalization)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = 3*(get_global_id(0) + width * get_global_id(1));
        LAB[i] /= normalization;
        LAB[i+1] /= normalization;
        LAB[i+2] /= normalization;
    }
}

kernel void delta_LAB(global float *LAB1,
                      global float *LAB2,
                      global float *delta,
                      int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = 3*(get_global_id(0) + width * get_global_id(1));
        delta[i/3] = LAB2[i] - LAB1[i];
    }
}

kernel void offset_LAB(global float *LAB,
                       float delta,
                      int width, int height)
{
    if ((get_global_id(0)<width) && (get_global_id(1) < height))
    {
        int i = 3*(get_global_id(0) + width * get_global_id(1));
        LAB[i] -=delta;
    }
}